# 使用增益对照协议（质量增益 / 效率增益 / 增益可验证性）

本题"使用增益"占 25 分，其中"增益可验证性 5 分"要求**用证据说明改善**，不能只写"笔记更结构化"。本协议给出可在单次运行内完成的对照记录方法。

## 1. 对照条件（必须一致）

| 项目 | 要求 |
|---|---|
| 原文 | 同一篇论文，同一文字层版本 |
| 解析方式 | 同一套章节切分规则与字段字典 |
| 任务要求 | 同一份 task.md 与输出字段要求 |
| 预算 | 同一模型、同一次运行预算（64 请求 / 900 秒） |
| 度量 | 同一组指标与同一判定口径（见第 3 节） |

不满足任一项，增益结论无效，写 `uncertainties` 说明对照不成立。

## 2. 两种记录方式（按可得性择一）

### 方式 A：同论文两次产出的可对比指标（首选）
若平台提供基础 Agent 的产出，或可复跑一次不加载 Skill 的条件，对两份笔记分别跑 `note_lint.py check`（**都对照同一份原文**），按第 3 节填表。

### 方式 B：单次运行内的两版笔记对照（无基础产出时）

1. 先按"通读一遍直接写笔记"的方式产出 `/app/work/notes_blind.json`（用通用摘要模板组织）；
2. 再按本 Skill 工作流，以 `outline.json` 为骨架产出 `/app/output/notes.json`；
3. 两版都对照同一份原文跑 `check`，比较下列计数的变化。

这种方式不是"跑两次模型"，而是**同一运行内的两版笔记**，成本低、可复核，且直接对应"是否减少了章节核对、锚点回查与返工"的效率增益。

## 3. 指标与口径（只报能算出来的）

| 指标 | 定义 | 采集方式 |
|---|---|---|
| 章节对齐率 | 笔记章节中能与原文等价章节对上的比例 | `note_report.section_alignment.matched_count / note_section_count` |
| 套模板章节数 | 笔记里有、原文中没有的章节 | `unmatched_count`，应为 0 |
| 漏章数 | 原文有、笔记没有的章节 | `missing_count`，应为 0 |
| 锚点可解析率 | 能解析且不越界 / 全部锚点 | `1 - unresolved_count / total` |
| 短引查得率 | evidence 能在原文找到的比例 | `1 - evidence.not_found_count / total`，应为 1 |
| 数值保真 | 笔记数值能在原文查到的比例 | `1 - numbers.orphan_count / 数值总数` |
| claim-evidence 一致 | claim 的数值都在自身 evidence 中的比例 | `numbers.claim_evidence_gap_count`，应为 0 |
| 字段覆盖 | 核心字段有笔记数 / 9 | `fields.covered_count` |
| 重复条目 | 同字段高度重复的笔记组数 | `duplicate_count`，应为 0 |
| 自相矛盾 | 同一对象多取值组数 | `contradiction_count`，应为 0 |
| 可检索性 | 有 confidence / 有 tags 的笔记比例 | `searchability.confidence_coverage` / `tag_coverage` |
| 返工轮次 | 从初稿到定稿的修正轮数 | `change_log` 条目数 |
| 耗时 | 从读原文到产出定稿的 wall time | 运行日志时间戳 |

## 4. 记录格式（写入 result.json）

```json
"gain_record": {
  "conditions": {"same_source": true, "same_rules": true, "same_budget": true, "same_task": true},
  "mode": "B_single_run_two_drafts",
  "baseline": {"notes": "/app/work/notes_blind.json", "section_match": 0, "unmatched": 0,
               "missing": 0, "anchor_unresolved": 0, "evidence_not_found": 0,
               "number_orphan": 0, "claim_evidence_gap": 0, "fields_covered": "0/9"},
  "with_skill": {"notes": "/app/output/notes.json", "section_match": 0, "unmatched": 0,
                 "missing": 0, "anchor_unresolved": 0, "evidence_not_found": 0,
                 "number_orphan": 0, "claim_evidence_gap": 0, "fields_covered": "0/9"},
  "delta_note": "套模板章节由 N 降至 0；锚点不可解析由 N 降至 0；短引查得率 a/b → b/b；字段覆盖 x/9 → y/9",
  "verifiable_artifacts": ["/app/output/note_report.json", "/app/output/note_report.md", "/app/output/index.json"]
}
```

## 5. 诚实性红线

- 不得编造对照数据、耗时或返工轮次；无法测量就写 `na` 并说明。
- 不得把平台提供的白板或官方结果写成自己的对照产出。
- 增益结论必须能由 `verifiable_artifacts` 里的文件复算出来；只写结论不附产物，视为不可验证。
- 不得为了让指标好看而减少笔记条数：`evidence_not_found` 为 0 但笔记只剩 3 条也说明覆盖不足，条数与保真度要一起报。
