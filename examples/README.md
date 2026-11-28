# 最小调用示例（示意）

以下用一份**合成的教学样例**（一篇 6 节的微型中文论文 + 一份含典型缺陷的笔记）走完从原文到核验报告、可检索索引的全流程，用于说明接口与输出。**不是正式案例答案，也不是任何真实论文的笔记。**

## 一、输入

原文 `/app/work/source.txt`（合成样例）：

```text
摘要
本文报道一种表面包覆的磷酸铁锂正极材料。

1 引言
容量衰减是磷酸铁锂的主要限制因素[1]。

2 实验方法
样品在 700 摄氏度下退火 6 小时，涂层厚度为 8 nm。

3 结果与讨论
包覆样在 1C 倍率下循环 500 次后容量保持率为 92%（图 2），
而未包覆样为 81%。扩散系数提高 3.5 倍。

4 结论
表面包覆可抑制副反应，但长期稳定性仍需验证。

参考文献
[1] Padhi AK, et al. J Electrochem Soc, 1997.
```

笔记 `/app/output/notes.json`（**故意保留 6 处典型缺陷**用于演示检出）：

| # | 缺陷 | 位置 |
|---|---|---|
| 1 | 章节名用英文 `Discussion`，但原文没有讨论节 | s5 |
| 2 | 锚点 `fig5`，但原文只有 2 张图 | 第 6 条 |
| 3 | evidence「复合电极展现出优异的首次库仑效率」原文根本没有 | 第 6 条 |
| 4 | claim 写「123%」，原文查不到 | 第 6 条 |
| 5 | claim 写「退火温度 800」，但自己的 evidence 说 700 | 第 4 条 |
| 6 | 第 5、7 条 claim 完全相同（重复条目） | s4 |

## 二、调用方式

```bash
L=/skills/weekly-skill/resources/scripts/note_lint.py

# 1) 抽原文骨架：拿到真实章节名与 max_fig / max_tab / max_eq（锚点校验边界）
python3 "$L" outline --source /app/work/source.txt --out /app/work

# 2) 按骨架写 notes.json 后核验
python3 "$L" check --source /app/work/source.txt \
                   --notes /app/output/notes.json --out /app/output

# 3) 生成可检索索引
python3 "$L" index --notes /app/output/notes.json --out /app/output
```

## 三、真实运行输出（本次实测，非虚构）

`outline` 的 stdout：

```json
{"ok": true, "section_count": 6, "paragraphs": 6, "pages": 0,
 "titles": ["摘要", "1 引言", "2 实验方法", "3 结果与讨论", "4 结论", "参考文献"]}
```

`check` 的 stdout：

```json
{"sections": {"source": 6, "notes": 5, "unmatched": 1, "missing": 2},
 "anchors": {"total": 8, "unresolved": 1, "unverifiable": 0},
 "fields_covered": "6/9", "evidence_not_found": 1,
 "number_orphan": 2, "duplicates": 1, "contradictions": 0, "glossary_missing": 1}
```

`note_report.md` 的关键几行：

```text
## 章节名在原文找不到（疑似套通用模板）（1）
- {"title": "Discussion", "reason": "原文标题列表中找不到等价章节——疑似套用通用模板", ...}

## 短引在原文查不到（1）
- {"index": 6, "evidence": "复合电极展现出优异的首次库仑效率", "reason": "原文中找不到该短引", ...}

## claim 的数值不在其 evidence 中（2）
- {"index": 4, "numbers_not_in_evidence": ["800"], ...}
- {"index": 6, "numbers_not_in_evidence": ["123"], ...}

## 重复笔记（1）
- {"index": [5, 7], "field": "result", "reason": "完全重复", ...}
```

读法：六处缺陷全部被抓到——

- `Discussion` 被判"套通用模板"（原文只有摘要/引言/实验方法/结果与讨论/结论/参考文献）；但笔记把 `Introduction` 写成英文**没有**误报，因为脚本走中英等价组（`Introduction`↔`引言`）。
- 锚点 `fig5` 被判 `unresolved`（原文最大图号是 2），而 `fig2` 通过。
- 编造的短引被判 `not_found`——这是"看起来很像论文里的句子但论文里根本没有"的典型。
- `123%` 在原文查不到（`number_orphan`）；`800` 与它自己的 evidence 里的 `700` 冲突（`claim_evidence_gap`）。
- 第 5、7 条 claim 完全重复。
- `fields_covered 6/9` 精确指出缺 `dataset` / `metric` / `limitation`。
- `missing 2` 指出漏了「结论」「参考文献」两节。

## 四、可检索索引

`index` 的 stdout 与 `index.md` 片段：

```json
{"ok": true, "notes": 8, "fields": 6, "sections": 5, "terms": 1}
```

```text
## 按字段
| 字段 | 条数 |
| result | 3 |
| research_question | 1 |
| method | 1 |
...

## 按章节
| 章节 | 条数 |
| Abstract | 1 |
| Introduction | 1 |
| Methods | 2 |
| Results | 3 |
```

索引是"用得上"的证据：把多篇论文的 `index.json` 按字段并排，就能做跨文献比较。

## 五、示意输出结构

见 `../resources/output_example.json`：`sections[].notes` 每条含 field/claim/evidence/anchor/confidence/tags，`verification` 与 `note_report` 带计数，`index` 给可检索性分布，`uncertainties` 记需人工确认项。

## 六、说明

- 上述样例文本为合成的教学用例，不代表任何真实论文的笔记质量。
- 真实评测由平台用固定的 3 个案例运行，参赛者不提供测试案例或白板。
- 提交包不含任何 `result.json`；运行时的结果只对应当次真实输入。
