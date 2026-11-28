#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
note_lint.py — 结构化论文笔记的「章节对齐 / 字段齐备 / 锚点可回查 / 可检索」核验器
（structured-paper-notes Skill 执行内核）

解决的问题：论文笔记最容易出事的地方不是"总结得不够全"，而是
  套了通用摘要模板（原文没有 Introduction 也写 Introduction）、
  evidence 短引是模型自己编的（原文根本没有这句话）、
  锚点指向不存在的章节/图号、笔记里的数值在原文查不到、
  同一变量在笔记里出现两个不同取值（自相矛盾）、
  以及最后交出来的东西搜不动、不能继续加工。
这些都能机械核对。

子命令：
  outline  从原文抽章节骨架（Markdown 标题 / 数字编号 / 中文编号 / 全大写节名）
  check    笔记 vs 原文：六类核验 → note_report.json + note_report.md
  index    由笔记生成可检索索引（按字段 / 术语 / 章节 / 置信度）→ index.md + index.json

用法：
  python3 note_lint.py outline --source /app/work/source.txt --out /app/work
  python3 note_lint.py check   --source /app/work/source.txt \\
                               --notes /app/output/notes.json --out /app/output
  python3 note_lint.py index   --notes /app/output/notes.json --out /app/output
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path


def _as_outfile(p, default_name):
    """--out 兼容层：传目录则写入目录下 default_name，传文件名则直接写该文件。"""
    path = Path(p)
    if path.is_dir() or not path.suffix:
        path = path / default_name
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _as_outdir(p):
    """--out 兼容层：传的是文件名时取其父目录，避免把文件路径当目录用而崩溃。"""
    path = Path(p)
    if path.suffix.lower() in (".json", ".md", ".txt", ".yaml", ".yml", ".csv", ".tex", ".bib"):
        path = path.parent if str(path.parent) not in ("", ".") else Path(".")
    path.mkdir(parents=True, exist_ok=True)
    return path

FIELDS = ["research_question", "motivation", "method", "dataset", "metric",
          "result", "conclusion", "limitation", "reproduce_info"]
CONFIDENCE = {"high", "medium", "low"}

# ---------- 章节抽取 ----------

MD_HEAD = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.M)
# 标题可由英文大写或中文起头（"1 引言" / "2. Methods" 都要认）
NUM_HEAD = re.compile(r"^\s*(\d+(?:\.\d+){0,3})[\.\s]+([A-Z\u4e00-\u9fff][^\n]{1,90})$", re.M)
CN_NUM_HEAD = re.compile(r"^\s*([一二三四五六七八九十]+)\s*[、\.]\s*([^\n]{2,60})$", re.M)
CAPS_HEAD = re.compile(r"^\s*([A-Z][A-Z\s\-]{3,40})\s*$", re.M)

# 中英章节名等价组：笔记把 Introduction 译成"引言"属正常对齐，不是套模板
SECTION_EQUIV = [
    ("abstract", ["abstract", "摘要", "summary"]),
    ("introduction", ["introduction", "引言", "前言", "绪论", "background", "研究背景", "introduction and background"]),
    ("related", ["related work", "related works", "相关工作", "literature review", "文献综述"]),
    ("methods", ["method", "methods", "methodology", "materials and methods", "experimental",
                 "experiments", "experimental section", "方法", "方法学", "实验", "实验部分",
                 "材料与方法", "实验方法"]),
    ("results", ["result", "results", "results and discussion", "结果", "结果与讨论", "结果与分析"]),
    ("discussion", ["discussion", "讨论"]),
    ("conclusion", ["conclusion", "conclusions", "结论", "结语", "总结"]),
    ("limitation", ["limitation", "limitations", "局限", "局限性", "研究局限"]),
    ("references", ["reference", "references", "bibliography", "参考文献"]),
    ("acknowledgment", ["acknowledgment", "acknowledgments", "acknowledgement",
                        "acknowledgements", "致谢"]),
]
_EQUIV = {}


def _build_equiv():
    if _EQUIV:
        return _EQUIV
    for canon, names in SECTION_EQUIV:
        for n in names:
            _EQUIV[norm(n)] = canon
    return _EQUIV


CN_SECTIONS = [x for _, names in SECTION_EQUIV for x in names if re.search(r"[\u4e00-\u9fff]", x)]
EN_SECTIONS = [x for _, names in SECTION_EQUIV for x in names if not re.search(r"[\u4e00-\u9fff]", x)]


def section_key(title):
    """把章节名映射到等价组 canonical；映射不到返回归一化原名"""
    eq = _build_equiv()
    n = norm(title)
    if n in eq:
        return eq[n]
    n2 = re.sub(r"^[\d一二三四五六七八九十]+(?:[\.\s、]+)?", "", n).strip()
    return eq.get(n2, n2 or n)


def read(p):
    try:
        return Path(p).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def norm(s):
    s = str(s or "").lower()
    s = re.sub(r"[\s\-_/·]+", " ", s)
    return s.strip(" \t\r\n.,;:!?。，；：！？()（）[]【】\"'")


def squash(s):
    """去掉所有空白与标点，用于短引是否存在于原文的判断"""
    return re.sub(r"[\s\u3000]+", "", str(s or "")).lower()


def extract_outline(src):
    heads = []

    for m in MD_HEAD.finditer(src):
        heads.append({"title": m.group(2).strip(), "level": len(m.group(1)),
                      "kind": "md", "pos": m.start()})
    for m in NUM_HEAD.finditer(src):
        heads.append({"title": f"{m.group(1)} {m.group(2)}".strip(), "level":
                      m.group(1).count(".") + 1, "kind": "numbered", "pos": m.start()})
    for m in CN_NUM_HEAD.finditer(src):
        heads.append({"title": m.group(2).strip(), "level": 1, "kind": "cn_numbered",
                      "pos": m.start()})
    for m in CAPS_HEAD.finditer(src):
        t = m.group(1).strip()
        if 1 <= len(t.split()) <= 5 and not t.endswith("."):
            heads.append({"title": t, "level": 1, "kind": "caps", "pos": m.start()})

    # 关键词兜底：整行很短且归一后命中已知节名（含带编号的中文节名）
    # 用 finditer 取真实位置，否则这些节会被排到全文最后，顺序判断就废了
    known = set(norm(x) for x in CN_SECTIONS + EN_SECTIONS)
    for m in re.finditer(r"^[ \t]*#{0,6}[ \t]*([^\n]{1,40}?)[ \t]*$", src, re.M):
        s = m.group(1).strip()
        if not s:
            continue
        cand = norm(s)
        cand = re.sub(r"^[\d一二三四五六七八九十]+(?:[\.\s、]+)?", "", cand).strip().rstrip(":：. ")
        if cand in known:
            heads.append({"title": s, "level": 1, "kind": "keyword", "pos": m.start()})

    # 去重并按位置排序
    seen, out = set(), []
    for h in sorted(heads, key=lambda x: (x["pos"] if x["pos"] >= 0 else 10 ** 9)):
        k = norm(h["title"])
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(h)
    return out


def max_ref(src, kind):
    pats = {"fig": r"(?:Fig(?:ure)?s?\.?|图)\s*(\d{1,3})",
            "tab": r"(?:Tables?\.?|表)\s*(\d{1,3})",
            "eq": r"(?:Eqs?\.?|公式)\s*\(?(\d{1,3})\)?"}
    nums = [int(x) for x in re.findall(pats[kind], src, re.I)]
    return max(nums) if nums else 0


def count_pages(src):
    return src.count("\f") + 1 if "\f" in src else 0


# ---------- 笔记读取 ----------

def load_notes(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else {"notes": data}


def flat_notes(obj):
    """同时支持 sections[].notes 嵌套与顶层 notes 平铺；返回 (notes, section_titles)"""
    notes, titles = [], []
    secs = obj.get("sections") or []
    for i, sec in enumerate(secs):
        t = str(sec.get("title") or sec.get("name") or "").strip()
        titles.append({"index": i, "title": t})
        for n in (sec.get("notes") or []):
            if isinstance(n, dict):
                nn = dict(n)
                nn.setdefault("_section", t)
                notes.append(nn)
    for n in (obj.get("notes") or []):
        if isinstance(n, dict):
            notes.append(dict(n))
    return notes, titles


# ---------- outline ----------

def cmd_outline(args):
    src = read(args.source)
    if not src:
        print(json.dumps({"ok": False, "error": "原文为空或路径不存在"}, ensure_ascii=False))
        return 1
    outline = extract_outline(src)
    paras = [b for b in re.split(r"\n\s*\n", src) if b.strip()]
    out = {"ok": True, "section_count": len(outline), "sections": outline,
           "paragraph_count": len(paras), "page_count": count_pages(src),
           "max_fig": max_ref(src, "fig"), "max_tab": max_ref(src, "tab"),
           "max_eq": max_ref(src, "eq")}
    _d = _as_outdir(args.out)
    p = _d / "outline.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "section_count": out["section_count"],
                      "paragraphs": out["paragraph_count"], "pages": out["page_count"],
                      "titles": [x["title"][:40] for x in outline[:20]], "out": str(p)},
                     ensure_ascii=False))
    return 0


# ---------- check ----------

ANCHOR_P = re.compile(r"^p(\d{1,4})\s*[:：]\s*(\d{1,4})$")
ANCHOR_SEC = re.compile(r"^(?:sec\s*[:：])?(.+?)\s*[:：/]\s*[ps]?(\d{1,4})$", re.I)
ANCHOR_SEC_ONLY = re.compile(r"^(?:sec\s*[:：])?(.+)$", re.I)
ANCHOR_REF = re.compile(r"^(fig|tab|eq|table|figure)\s*(\d{1,3})[a-z]?$", re.I)
ANCHOR_LINE = re.compile(r"^line\s*[:：]\s*(\d+)\s*-\s*(\d+)$", re.I)
# 页:行 与 单行 两种最常见写法（p1:L3 / L12 / line 12），旧实现只认 p1:3 与 line:3-9，
# 遇到 p1:L3 会落到"不符合任何可识别格式"，把正确锚点全判成 unresolved。
ANCHOR_PL = re.compile(r"^p?(\d{1,4})\s*[:：]\s*[Ll]\s*(\d{1,4})$")
ANCHOR_L = re.compile(r"^(?:[Ll]|line)\s*[:：]?\s*(\d{1,4})$")


def _section_hit(name, titles):
    """章节名是否命中原文标题（走等价组 + 子串回退）"""
    k = section_key(name)
    if any(section_key(t) == k for t in titles):
        return True
    n = norm(name)
    return any(n and (n in norm(t) or norm(t) in n) for t in titles)


def check_anchor(anchor, ctx):
    """返回 (status, detail)：status ∈ ok / unresolved / unverifiable"""
    a = str(anchor or "").strip()
    if not a:
        return "unresolved", "anchor 为空"
    total_lines = ctx.get("lines") or 0
    for piece in [x.strip() for x in re.split(r"[;；]", a) if x.strip()]:
        m = ANCHOR_LINE.match(piece)
        if m:
            continue
        m = ANCHOR_PL.match(piece)
        if m:
            page, line_no = int(m.group(1)), int(m.group(2))
            if ctx["pages"] and page > ctx["pages"]:
                return "unresolved", f"页号 {page} 超出原文页数 {ctx['pages']}"
            if total_lines and line_no > total_lines:
                return "unresolved", f"行号 {line_no} 超出原文总行数 {total_lines}"
            continue
        m = ANCHOR_L.match(piece)
        if m:
            line_no = int(m.group(1))
            if total_lines and line_no > total_lines:
                return "unresolved", f"行号 {line_no} 超出原文总行数 {total_lines}"
            continue
        m = ANCHOR_P.match(piece)
        if m:
            page = int(m.group(1))
            if ctx["pages"] and page > ctx["pages"]:
                return "unresolved", f"页号 {page} 超出原文页数 {ctx['pages']}"
            if not ctx["pages"]:
                return "unverifiable", "原文无分页符，页号无法机械校验"
            if int(m.group(2)) > ctx["paragraphs"]:
                return "unresolved", f"段号 {m.group(2)} 超出原文段落数 {ctx['paragraphs']}"
            continue
        m = ANCHOR_REF.match(piece)
        if m:
            kind = {"figure": "fig", "table": "tab"}.get(m.group(1).lower(), m.group(1).lower())
            n = int(m.group(2))
            cap = ctx["max_" + kind]
            if cap == 0:
                return "unverifiable", f"原文未检出任何 {kind} 编号，无法校验"
            if n > cap:
                return "unresolved", f"{kind}{n} 超出原文最大编号 {kind}{cap}"
            continue
        m = ANCHOR_SEC.match(piece)
        if m:
            name = m.group(1)
            if not norm(name):
                return "unresolved", "章节名为空"
            if _section_hit(name, ctx["titles"]):
                continue
            return "unresolved", f"章节「{name}」不在原文标题列表中"
        m = ANCHOR_SEC_ONLY.match(piece)
        if m:
            name = m.group(1)
            if _section_hit(name, ctx["titles"]):
                continue
            return "unresolved", f"锚点「{piece}」不符合任何可识别格式，且不是原文章节名"
    return "ok", ""


def cmd_check(args):
    src = read(args.source)
    obj = load_notes(args.notes)
    if not src:
        print(json.dumps({"ok": False, "error": "原文为空/路径不存在"}, ensure_ascii=False))
        return 1
    if obj is None:
        print(json.dumps({"ok": False, "error": "notes.json 无法解析为 JSON"}, ensure_ascii=False))
        return 1

    notes, sec_titles = flat_notes(obj)
    outline = extract_outline(src)
    ctx = {"pages": count_pages(src), "lines": len(src.splitlines()),
           "paragraphs": len([b for b in re.split(r"\n\s*\n", src) if b.strip()]),
           "max_fig": max_ref(src, "fig"), "max_tab": max_ref(src, "tab"),
           "max_eq": max_ref(src, "eq"),
           "titles": [h["title"] for h in outline]}

    # ---- 1) 章节对齐（中英章节名走等价组，翻译过的节名不算套模板）----
    src_keys = [section_key(t) for t in ctx["titles"]]
    sec_match, sec_unmatched = [], []
    for st in sec_titles:
        n = norm(st["title"])
        if not n:
            sec_unmatched.append({"title": st["title"], "reason": "章节标题为空",
                                  "action": "补章节标题"})
            continue
        k = section_key(st["title"])
        if k in src_keys:
            sec_match.append({"title": st["title"], "matched_source_title":
                              ctx["titles"][src_keys.index(k)]})
        else:
            hit = [t for t in ctx["titles"] if n in norm(t) or norm(t) in n]
            if hit:
                sec_match.append({"title": st["title"], "matched_source_title": hit[0]})
            else:
                sec_unmatched.append({
                    "title": st["title"],
                    "reason": "原文标题列表中找不到等价章节——疑似套用通用模板",
                    "action": "改用原文真实章节名；若原文该节确实不存在，删除该章节而非空着"})
    # 漏章：原文有、笔记没有
    note_keys = [section_key(st["title"]) for st in sec_titles if norm(st["title"])]
    sec_missing = [t for t, k in zip(ctx["titles"], src_keys) if k not in note_keys]
    # 顺序：笔记章节在原文中的出现次序是否单调
    order_idx = []
    for st in sec_titles:
        k = section_key(st["title"])
        if k in src_keys:
            order_idx.append((st["title"], src_keys.index(k)))
    order_mismatch = []
    for k in range(1, len(order_idx)):
        if order_idx[k][1] < order_idx[k - 1][1]:
            order_mismatch.append({"previous": order_idx[k - 1][0], "current": order_idx[k][0],
                                   "action": "笔记章节顺序与原文相反，按原文顺序重排"})

    # ---- 2) 锚点可回查 ----
    anchor_unresolved, anchor_unverifiable = [], []
    for i, n in enumerate(notes, 1):
        st, detail = check_anchor(n.get("anchor"), ctx)
        rec = {"index": i, "field": n.get("field"), "anchor": n.get("anchor"),
               "claim": str(n.get("claim") or "")[:120], "detail": detail}
        if st == "unresolved":
            anchor_unresolved.append(rec)
        elif st == "unverifiable":
            anchor_unverifiable.append(rec)

    # ---- 3) 字段覆盖 ----
    got = Counter(str(n.get("field") or "").strip() for n in notes)
    field_covered = [f for f in FIELDS if got.get(f)]
    field_missing = [{"field": f, "action": "补该字段笔记；原文确实未述则写「原文未述」并记入 uncertainties"}
                     for f in FIELDS if not got.get(f)]
    field_unknown = [{"field": f, "count": c} for f, c in got.items()
                     if f and f not in FIELDS]
    no_field = sum(1 for n in notes if not str(n.get("field") or "").strip())

    # ---- 4) evidence 是否真在原文 ----
    src_squash = squash(src)
    ev_missing = []
    for i, n in enumerate(notes, 1):
        ev = str(n.get("evidence") or "").strip()
        if not ev:
            ev_missing.append({"index": i, "field": n.get("field"), "reason": "evidence 为空",
                               "action": "补原文短引（15–40 词），空短引等于无法核验"})
            continue
        key = squash(re.sub(r"[…\.]{3,}|……", "", ev))
        if len(key) < 8:
            ev_missing.append({"index": i, "field": n.get("field"), "evidence": ev[:80],
                               "reason": "短引过短，无法核验", "action": "扩到 15–40 词"})
            continue
        if key not in src_squash:
            ev_missing.append({"index": i, "field": n.get("field"), "evidence": ev[:120],
                               "anchor": n.get("anchor"),
                               "reason": "原文中找不到该短引",
                               "action": "核对是否改写/拼接了原文，或换成原文原句；编造引文必须删除"})

    # ---- 5) 笔记数值是否在原文 ----
    NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?:[eE][+-]?\d+)?%?")
    CITE = re.compile(r"\[\d{1,3}(?:\s*[,\-–]\s*\d{1,3})*\]")
    src_nums = Counter(x.rstrip("%") for x in NUM.findall(CITE.sub(" ", src)))
    num_orphan = []
    for i, n in enumerate(notes, 1):
        text = CITE.sub(" ", f"{n.get('claim') or ''} {n.get('evidence') or ''}")
        for v in NUM.findall(text):
            v = v.rstrip("%")
            if src_nums.get(v, 0) == 0:
                num_orphan.append({"index": i, "field": n.get("field"), "value": v,
                                   "claim": str(n.get("claim") or "")[:100],
                                   "action": "该数值在原文中查不到：核对是否改写/换算/编造"})
    # 去重同一 index+value
    seen_nv, num_orphan_u = set(), []
    for x in num_orphan:
        k = (x["index"], x["value"])
        if k in seen_nv:
            continue
        seen_nv.add(k)
        num_orphan_u.append(x)
    num_orphan = num_orphan_u[:60]

    # claim 与它自己的 evidence 数值不一致（抄错/换算/串行的高发点）
    claim_ev_gap = []
    for i, n in enumerate(notes, 1):
        claim = CITE.sub(" ", str(n.get("claim") or ""))
        ev = CITE.sub(" ", str(n.get("evidence") or ""))
        nc = set(x.rstrip("%") for x in NUM.findall(claim))
        ne = set(x.rstrip("%") for x in NUM.findall(ev))
        extra = nc - ne
        if extra and ev:
            claim_ev_gap.append({"index": i, "field": n.get("field"),
                                 "claim": str(n.get("claim"))[:120],
                                 "evidence": str(n.get("evidence"))[:120],
                                 "numbers_not_in_evidence": sorted(extra),
                                 "action": "该数值不在本条 evidence 中：确认是否来自本锚点之外的其他段落；"
                                           "若无法定位到原文，必须改写或降低 confidence"})
    claim_ev_gap = claim_ev_gap[:40]

    # ---- 6) 重复与自相矛盾 ----
    dup = []
    for i in range(len(notes)):
        for j in range(i + 1, len(notes)):
            a, b = notes[i], notes[j]
            if str(a.get("field") or "") != str(b.get("field") or ""):
                continue
            ca = norm(a.get("claim"))
            cb = norm(b.get("claim"))
            if not ca or not cb:
                continue
            if ca == cb:
                dup.append({"index": (i + 1, j + 1), "field": a.get("field"),
                            "claim": str(a.get("claim"))[:100], "reason": "完全重复",
                            "action": "合并为一条并保留多锚点"})
                continue
            r = SequenceMatcher(None, ca, cb, autojunk=False).ratio()
            if r >= 0.92:
                dup.append({"index": (i + 1, j + 1), "field": a.get("field"), "similarity": round(r, 3),
                            "claim": str(a.get("claim"))[:100], "reason": "高度重复",
                            "action": "合并或明确区分二者差异"})

    # 同一指标出现不同取值
    KEYVAL = re.compile(r"([A-Za-z\u4e00-\u9fff][\w\u4e00-\u9fff\-]{1,24})\s*(?:为|是|=|of|at|:)?\s*"
                        r"(\d+(?:\.\d+)?)\s*(%|mg|g|kg|mL|L|nm|mm|cm|h|min|s|K|℃|°C|eV|MPa|GPa|mA|V)?")
    kv = defaultdict(set)
    for i, n in enumerate(notes, 1):
        for m in KEYVAL.finditer(str(n.get("claim") or "")):
            k = (norm(m.group(1)), m.group(3) or "")
            kv[k].add((m.group(2), i))
    contradictions = []
    for (k, unit), vals in kv.items():
        distinct = {v for v, _ in vals}
        if len(distinct) > 1 and k:
            contradictions.append({"term": k, "unit": unit,
                                   "values": sorted([{"value": v, "note_index": i} for v, i in vals],
                                                    key=lambda x: x["note_index"]),
                                   "action": "同一对象在笔记中出现多个取值：核对哪一处对应原文，另一处改正或说明条件差异"})
    contradictions = contradictions[:40]

    # ---- 7) 术语 ----
    glossary = obj.get("glossary") or []
    g_missing, g_drift = [], []
    all_note_text = squash(" ".join(str(n.get("claim") or "") + str(n.get("evidence") or "") for n in notes))
    for g in glossary:
        if not isinstance(g, dict):
            continue
        term = str(g.get("term") or "").strip()
        canon = str(g.get("canonical") or g.get("zh") or "").strip()
        if not canon:
            g_missing.append({"term": term, "reason": "未给 canonical 写法"})
            continue
        if squash(canon) not in all_note_text:
            g_missing.append({"term": term, "canonical": canon,
                              "action": "术语表给的统一写法在笔记正文中未出现，确认是否漏用"})
        forms = set(re.findall(re.escape(canon), " ".join(str(n.get("claim") or "") for n in notes)))
        if len(forms) > 1:
            g_drift.append({"term": term, "canonical": canon, "forms": sorted(forms),
                            "action": "同一术语多种写法，统一为 canonical"})

    # ---- 8) 可检索性 ----
    with_conf = sum(1 for n in notes if str(n.get("confidence") or "").strip() in CONFIDENCE)
    with_tags = sum(1 for n in notes if (n.get("tags") or n.get("keywords")))
    searchability = {
        "notes_with_confidence": with_conf, "confidence_coverage": round(with_conf / max(1, len(notes)), 4),
        "notes_with_tags": with_tags, "tag_coverage": round(with_tags / max(1, len(notes)), 4),
        "field_distribution": dict(got),
        "has_glossary": bool(glossary),
    }

    report = {
        "ok": True, "source": str(args.source), "notes": str(args.notes),
        "section_alignment": {
            "source_section_count": len(outline), "note_section_count": len(sec_titles),
            "matched_count": len(sec_match), "unmatched": sec_unmatched[:40],
            "unmatched_count": len(sec_unmatched),
            "missing_from_notes": sec_missing[:40], "missing_count": len(sec_missing),
            "order_mismatch": order_mismatch[:20], "order_mismatch_count": len(order_mismatch),
        },
        "anchors": {"total": len(notes), "unresolved": anchor_unresolved[:40],
                    "unresolved_count": len(anchor_unresolved),
                    "unverifiable": anchor_unverifiable[:40],
                    "unverifiable_count": len(anchor_unverifiable)},
        "fields": {"required": FIELDS, "covered": field_covered,
                   "covered_count": len(field_covered), "missing": field_missing,
                   "missing_count": len(field_missing),
                   "unknown_field": field_unknown, "notes_without_field": no_field},
        "evidence": {"total": len(notes), "not_found": ev_missing[:40],
                     "not_found_count": len(ev_missing)},
        "numbers": {"orphan": num_orphan, "orphan_count": len(num_orphan),
                    "claim_evidence_gap": claim_ev_gap,
                    "claim_evidence_gap_count": len(claim_ev_gap)},
        "duplicates": dup[:40], "duplicate_count": len(dup),
        "contradictions": contradictions, "contradiction_count": len(contradictions),
        "glossary": {"terms": len(glossary), "missing": g_missing[:40],
                     "missing_count": len(g_missing), "drift": g_drift[:40],
                     "drift_count": len(g_drift)},
        "searchability": searchability,
        "verification_hint": {
            "section_alignment": (
                f"原文 {len(outline)} 节 / 笔记 {len(sec_titles)} 节；匹配 {len(sec_match)}；"
                f"套模板嫌疑 {len(sec_unmatched)}；漏章 {len(sec_missing)}；顺序错 {len(order_mismatch)}"),
            "anchor_retrievability": (
                f"锚点 {len(notes)} 条；无法解析 {len(anchor_unresolved)}；"
                f"无法机械校验 {len(anchor_unverifiable)}；"
                f"可校验成功率 {round((len(notes) - len(anchor_unresolved)) / max(1, len(notes)), 4)}"),
            "field_coverage": f"核心字段 {len(field_covered)} / {len(FIELDS)}；无字段笔记 {no_field} 条",
            "evidence_fidelity": f"短引 {len(notes)} 条；原文查不到 {len(ev_missing)} 条",
            "numeric_fidelity": (f"数值在原文查不到 {len(num_orphan)} 项；"
                                 f"claim 数值不在其 evidence 中 {len(claim_ev_gap)} 条"),
            "consistency": f"重复笔记 {len(dup)} 组；同一对象多取值 {len(contradictions)} 组",
            "reusability": (f"confidence 覆盖 {searchability['confidence_coverage']}；"
                            f"tags 覆盖 {searchability['tag_coverage']}；术语表 {len(glossary)} 条"),
        },
    }

    outdir = _as_outdir(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "note_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(report, outdir / "note_report.md")
    print(json.dumps({"sections": {"source": len(outline), "notes": len(sec_titles),
                                   "unmatched": len(sec_unmatched), "missing": len(sec_missing)},
                      "anchors": {"total": len(notes), "unresolved": len(anchor_unresolved),
                                  "unverifiable": len(anchor_unverifiable)},
                      "fields_covered": f"{len(field_covered)}/{len(FIELDS)}",
                      "evidence_not_found": len(ev_missing),
                      "number_orphan": len(num_orphan),
                      "duplicates": len(dup),
                      "contradictions": len(contradictions),
                      "glossary_missing": len(g_missing)}, ensure_ascii=False))
    return 0


def write_md(r, path):
    md = ["# 结构化笔记核验报告（对得上 / 留得住 / 找得回 / 用得上）", "",
          f"- 章节对齐：原文 {r['section_alignment']['source_section_count']} 节 / 笔记 "
          f"{r['section_alignment']['note_section_count']} 节；匹配 "
          f"{r['section_alignment']['matched_count']}；套模板嫌疑 "
          f"{r['section_alignment']['unmatched_count']}；漏章 {r['section_alignment']['missing_count']}"
          f"；顺序错 {r['section_alignment']['order_mismatch_count']}",
          f"- 锚点：{r['anchors']['total']} 条；无法解析 {r['anchors']['unresolved_count']}"
          f"；无法机械校验 {r['anchors']['unverifiable_count']}",
          f"- 字段：核心字段 {r['fields']['covered_count']} / {len(r['fields']['required'])}"
          f"；无字段笔记 {r['fields']['notes_without_field']} 条",
          f"- 证据：短引原文查不到 {r['evidence']['not_found_count']} 条"
          f"；数值原文查不到 {r['numbers']['orphan_count']} 项"
          f"；claim 数值不在 evidence 中 {r['numbers']['claim_evidence_gap_count']} 条",
          f"- 一致性：重复 {r['duplicate_count']} 组；同一对象多取值 {r['contradiction_count']} 组",
          f"- 术语：{r['glossary']['terms']} 条；未落实 {r['glossary']['missing_count']}"
          f"；写法漂移 {r['glossary']['drift_count']}", ""]
    secs = [
        ("章节名在原文找不到（疑似套通用模板）", r["section_alignment"]["unmatched"]),
        ("原文有但笔记缺的章节", [{"title": t} for t in r["section_alignment"]["missing_from_notes"]]),
        ("章节顺序与原文相反", r["section_alignment"]["order_mismatch"]),
        ("锚点无法解析", r["anchors"]["unresolved"]),
        ("锚点无法机械校验（需人工抽查）", r["anchors"]["unverifiable"]),
        ("字段缺口", r["fields"]["missing"]),
        ("字段名不在字典内", r["fields"]["unknown_field"]),
        ("短引在原文查不到", r["evidence"]["not_found"]),
        ("数值在原文查不到", r["numbers"]["orphan"]),
        ("claim 的数值不在其 evidence 中", r["numbers"]["claim_evidence_gap"]),
        ("重复笔记", r["duplicates"]),
        ("同一对象出现多个取值", r["contradictions"]),
        ("术语表未落实 / 写法漂移", r["glossary"]["missing"] + r["glossary"]["drift"]),
    ]
    for label, items in secs:
        if items:
            md += [f"## {label}（{len(items)}）", ""]
            for it in items[:20]:
                md.append(f"- {json.dumps(it, ensure_ascii=False)[:260]}")
            md.append("")
    md += ["## 自检口径（可直接写入 verification）", ""]
    md += [f"- `{k}`：{v}" for k, v in r["verification_hint"].items()]
    path.write_text("\n".join(md), encoding="utf-8")


# ---------- index ----------

def cmd_index(args):
    obj = load_notes(args.notes)
    if obj is None:
        print(json.dumps({"ok": False, "error": "notes.json 无法解析为 JSON"}, ensure_ascii=False))
        return 1
    notes, sec_titles = flat_notes(obj)
    by_field, by_section, by_term = defaultdict(list), defaultdict(list), defaultdict(list)
    for i, n in enumerate(notes, 1):
        f = str(n.get("field") or "unfiled").strip() or "unfiled"
        sec = str(n.get("_section") or n.get("section") or "").strip() or "（未标章节）"
        rec = {"index": i, "claim": n.get("claim"), "anchor": n.get("anchor"),
               "confidence": n.get("confidence")}
        by_field[f].append(rec)
        by_section[sec].append(rec)
        for t in (n.get("tags") or n.get("keywords") or []):
            by_term[str(t)].append(rec)

    idx = {"case_id": obj.get("case_id"), "note_count": len(notes),
           "by_field": {k: len(v) for k, v in by_field.items()},
           "by_section": {k: len(v) for k, v in by_section.items()},
           "terms": sorted(by_term)}
    outdir = _as_outdir(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")

    md = ["# 笔记索引（可检索）", "", f"- case_id: `{obj.get('case_id')}`", f"- 笔记条数: {len(notes)}", ""]
    md += ["## 按字段", "", "| 字段 | 条数 |", "|---|---|"]
    md += [f"| {k} | {len(v)} |" for k, v in sorted(by_field.items(), key=lambda x: -len(x[1]))]
    md += ["", "## 按章节", "", "| 章节 | 条数 |", "|---|---|"]
    md += [f"| {k} | {len(v)} |" for k, v in by_section.items()]
    if by_term:
        md += ["", "## 按标签 / 术语", "", "| 术语 | 条数 |", "|---|---|"]
        md += [f"| {k} | {len(v)} |" for k, v in sorted(by_term.items(), key=lambda x: -len(x[1]))]
    md += ["", "## 条目（按字段）", ""]
    for f, items in sorted(by_field.items()):
        md += [f"### {f}（{len(items)}）", ""]
        for it in items:
            md.append(f"- [{it['index']}] {str(it['claim'])[:160]}  \n  锚点：`{it['anchor']}`"
                      f"｜置信度：{it['confidence']}")
        md.append("")
    (outdir / "index.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({"ok": True, "notes": len(notes), "fields": len(by_field),
                      "sections": len(by_section), "terms": len(by_term),
                      "out": [str(outdir / "index.md"), str(outdir / "index.json")]},
                     ensure_ascii=False))
    return 0



def _blank_contract_value(v):
    """合同字段的空占位：形状对、内容空，绝不复制合同示例当作答案。"""
    if isinstance(v, dict):
        return {}
    if isinstance(v, list):
        return []
    if isinstance(v, bool):
        return False
    if isinstance(v, (int, float)):
        return 0
    return ""

def cmd_init(args):
    """读真实 case.json，先落盘含全部合同字段的 partial result.json 骨架。"""
    try:
        case = json.loads(Path(args.case).read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok": False, "error": "case.json 无法读取: %s" % exc}, ensure_ascii=False))
        return 1
    if not isinstance(case, dict):
        print(json.dumps({"ok": False, "error": "case.json 顶层必须是对象"}, ensure_ascii=False))
        return 1
    contract = case.get("output_contract") or {}
    if not isinstance(contract, dict):
        contract = {}
    skeleton = {
        "case_id": case.get("case_id", "N/A"),
        "status": "partial",
        "paper_meta": {"title": "原文未述", "authors": "原文未述", "year": "原文未述", "source": "原文未述"},
        "sections": [],
        "notes": [],
        "glossary": [],
        "verification": {k: {"result": "na", "evidence": "pending"} for k in
                         ["section_alignment", "anchor_retrievability", "field_coverage", "evidence_fidelity",
                          "numeric_fidelity", "consistency", "reusability", "no_new_facts"]},
        "note_report": {},
        "index": {},
        "gain_record": {"conditions": "na", "mode": "na", "baseline": "na", "with_skill": "na",
                        "delta_note": "尚未产生对照产物", "verifiable_artifacts": []},
        "uncertainties": [],
        "sources": [str(args.case)],
        "change_log": [{"issue": "initialized", "fix": "先写合同骨架，内容待真实笔记填充",
                        "location": "result.json", "verified": "file exists"}],

    }
    for key, value in contract.items():
        if key not in skeleton or skeleton[key] in (None, "", [], {}):
            skeleton[key] = _blank_contract_value(value)
    skeleton["contract_values"] = contract
    outdir = _as_outdir(args.out)
    target = outdir / "result.json"
    target.write_text(json.dumps(skeleton, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "case_id": skeleton["case_id"],
                      "contract_fields": len(contract), "status": "partial", "out": str(target)},
                     ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description="结构化论文笔记核验器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ini = sub.add_parser("init"); ini.add_argument("--case", required=True); ini.add_argument("--out", required=True)

    o = sub.add_parser("outline"); o.add_argument("--source", required=True); o.add_argument("--out", required=True)
    c = sub.add_parser("check"); c.add_argument("--source", required=True)
    c.add_argument("--notes", required=True); c.add_argument("--out", required=True)
    i = sub.add_parser("index"); i.add_argument("--notes", required=True); i.add_argument("--out", required=True)

    a = ap.parse_args()
    return {"outline": cmd_outline, "check": cmd_check, "index": cmd_index, "init": cmd_init}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
