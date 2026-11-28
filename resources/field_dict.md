# 字段字典

| 字段 | 含义 | 抽取要点 |
|---|---|---|
| research_question | 研究问题 | 论文试图解决什么，原文表述优先 |
| motivation | 研究动机 | 为什么重要，现有方法的不足 |
| method | 方法 | 算法/实验/表征手段，关键步骤 |
| dataset | 数据 | 数据集名称、规模、来源、划分 |
| metric | 指标 | 评价指标定义与计算方式 |
| result | 结果 | 具体数值、趋势、对比，保留单位 |
| conclusion | 结论 | 作者主张，注意限定强度 |
| limitation | 限制 | 作者自述或可推断的局限 |
| reproduce_info | 复现信息 | 参数、软件版本、实验条件 |
| term | 术语 | 关键术语、缩写、符号的统一写法 |

## 每条笔记结构

```
{
  "field": "result",
  "claim": "在X条件下Y指标达到Z（忠实转述）",
  "evidence": "原文短引（15-40词）",
  "anchor": "p3:2 或 results:4 或 fig2",
  "confidence": "high"
}
```

## confidence 判定
- high：原文明确表述，锚点清晰，evidence 短引可逐字回查
- medium：需轻微推断或多处合并（推断部分要在 claim 中标出）
- low：表述模糊、图表缺失、需人工确认，或锚点回查未通过

## 锚点（anchor）格式与回查

| 形式 | 示例 | 脚本校验方式 |
|---|---|---|
| `p<页>:<段>` | `p3:2` | 页号 ≤ 原文分页数、段号 ≤ 原文段落数；原文无分页符时判 `unverifiable` |
| `sec:<章节名>` / `sec:<章节名>/p<段>` | `sec:Methods/p2`、`sec:引言` | 章节名须与原文标题等价（中英等价组，`Introduction`↔`引言`） |
| `fig<号>` / `tab<号>` / `eq<号>` | `fig2`、`tab1`、`eq4` | 编号 ≤ 原文该类型最大编号；原文未检出该类型则判 `unverifiable` |
| `line:<起>-<止>` | `line:41-58` | 仅格式校验，需人工确认 |

校验三态，**含义完全不同，不要混用**：

- `ok`：可解析且未越界。
- `unresolved`：指向不存在的章节，或 `fig5` 而原文只有 2 张图——**必须改**，这类锚点是猜的。
- `unverifiable`：原文无分页符等客观原因无法机械校验——**必须人工抽查**并在 `verification` 写清抽查数与片段。

回查方法：按 anchor 定位原文，确认 evidence 短引出现在该位置；不一致则修正 evidence/anchor，或降低 confidence 并写入 `uncertainties`。

## `notes.json` 结构（脚本入口）

```json
{
  "case_id": "从 case.json 回填",
  "paper_meta": {"title": "", "authors": "", "year": "", "source": "", "version": ""},
  "sections": [
    {"section_id": "s1", "title": "引言",
     "notes": [
       {"field": "research_question", "claim": "……", "evidence": "……短引……",
        "anchor": "sec:引言/p1", "confidence": "high", "tags": ["包覆", "容量衰减"]}
     ]}
  ],
  "glossary": [{"term": "capacity retention", "canonical": "容量保持率", "anchor": "sec:结果与讨论/p1"}]
}
```

- `sections[].notes` 嵌套结构与顶层 `notes` 数组**两种都支持**，但键名必须是这两者之一。
- `title` 用**原文真实章节名**；`glossary` 的 `canonical` 必须真的出现在某条 claim 或 evidence 里，否则脚本判"未落实"。
- `tags` 建议给 2–4 个；`searchability.tag_coverage` 直接反映笔记是否"用得上"。

## claim 与 evidence 的硬规则

1. **evidence 必须是原文原句**（15–40 词），不得改写、拼接、摘要化；脚本会做去空白去标点的子串比对，改写即判 `not_found`。
2. **claim 里的每个数值都要能在同条 evidence 中找到**；跨段合并的数值要么拆成两条笔记，要么在该条 `evidence` 里给出对应的多句短引——否则会判 `claim_evidence_gap`。
3. 数值必须能在**原文**里查到（允许换算，但换算要在 claim 中写明"按 … 换算"）。
4. 同一字段不要留两条几乎相同的笔记；合并后保留多个锚点。

## 作者主张 vs 推断
- 作者明确写的限制、结论 → confidence high，evidence 用原话短引。
- 由方法/数据推断出的限制、判断 → confidence medium/low，claim 中写明"据…推断"，不得冒充作者主张。
