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
- high：原文明确表述，锚点清晰
- medium：需轻微推断或多处合并
- low：表述模糊、图表缺失、需人工确认
