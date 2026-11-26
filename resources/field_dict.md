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
- `p<页>:<段落号>`：如 p3:2 表示第 3 页第 2 段
- `<章节>:<段落号>`：如 results:4 表示结果章第 4 段
- `fig<号>` / `tab<号>` / `eq<号>`：图表公式位置
- 回查方法：按 anchor 定位原文，确认 evidence 短引出现在该位置；不一致则修正 evidence/anchor 或降低 confidence 并写入 uncertainties。逐条统计"回查成功数/总数"写进 verification。

## 作者主张 vs 推断
- 作者明确写的限制、结论 → confidence high，evidence 用原话短引。
- 由方法/数据推断出的限制、判断 → confidence medium/low，claim 中写明"据…推断"，不得冒充作者主张。
