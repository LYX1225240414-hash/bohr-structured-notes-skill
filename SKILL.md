---
name: structured-paper-notes
description: 把科研论文转化为章节对齐、字段齐备、逐条可回链的中文结构化笔记。当用户要求读论文做笔记、提取研究问题/方法/数据/结果/结论/限制、生成可检索的文献卡片，或需要每条论断都能回到原文具体位置时时使用。适用于期刊论文、会议论文、预印本；支持中英文文献。
---

# 文献总结与结构化笔记：章节对齐、字段齐备、锚点可回链

把真实论文变成**能继续用、能复核、能检索**的结构化笔记，而不是一段压缩后的通读摘要。核心是三层：**章节对齐 → 字段抽取 → 锚点回链**。每一条论断都要能回答两个问题："它来自原文哪里？"和"我怎么验证它没被改写？"

## 何时使用

- 读论文做笔记，要求按章节组织、字段化输出。
- 需要每条论断、数值、变量、方法条件都能回到原文具体位置。
- 需要覆盖研究问题、数据、方法、结果、结论、限制等完整要素。

不适用：无原文材料、仅要求一句话极简摘要、非科研文档。

## 运行环境与输出路径（重要）

- 输入材料在 `/input/case.json`（含 case_id 与任务字段）与同目录 task.md；原文按题目给出的材料/文件读取，**不要用文件名或标签推断内容**。
- 工作文件放在 `/app/work`；**最终结果写到 `/app/output/result.json`**，可编辑中间产物也放 `/app/output`。
- `result.json` 必须包含输入里的 `case_id`（原样回填，不得改写）与题目 `output_contract` 要求的全部字段；本 Skill 定义的字段是最小集，若合同字段更多要一并输出。
- 预算内尽早写出诚实的部分结果再增量完善；3 个案例、每条件 3 次运行由平台安排，参赛者不提供测试案例或白板。

## 输入输出

输入：论文文本或文件路径（PDF / TXT / MD）；可选：关注方向、目标字段、是否需要术语表。

输出：`result.json`，字段如下（case_id 必填且原样回填）：

| 字段 | 要求 |
|---|---|
| case_id | 输入标识，从 case.json 原样回填；确实没有才填 N/A |
| status | success / partial / unable / refused；部分完成必须指明未完成范围与可人工接管位置 |
| paper_meta | 标题、作者、年份、来源、版本标识（缺失填"原文未述"，不猜） |
| sections | 章节数组，每项含 section_id、title、notes |
| notes | 笔记数组，每条含 field / claim / evidence / anchor / confidence |
| glossary | 关键术语与符号表（term / canonical / anchor） |
| verification | 字段覆盖、锚点有效性、事实一致性自检结论，附具体计数 |
| uncertainties | 无法判断、材料缺失、双栏错序、图表公式不可解析等条目及原因 |
| sources | 使用的输入文件/页码范围清单，便于复核输入边界 |
| change_log | 自检回修记录：每处改动、原因、修正后结果 |

**字段字典（notes.field）**：`research_question` / `motivation` / `method` / `dataset` / `metric` / `result` / `conclusion` / `limitation` / `reproduce_info` / `term`。

**锚点格式（anchor）**：`p<页>:<段落号>` 或 `<章节>:<段落号>` 或 `fig<号>/tab<号>/eq<号>`，必须指向原文真实位置。

## 工作流

### 第 1 步：读取输入边界
读取实际文件，不用文件名或标签推断内容。确认页数、语言、单双栏、是否有图表公式、是否扫描件。缺文件 → status: unable 并说明缺什么。扫描件尝试 OCR，失败写入 uncertainties。把输入清单记入 sources。

### 第 2 步：章节对齐
按原文真实标题切分章节（摘要/引言/相关/方法/实验/结果/讨论/结论），保留 section_id 与标题原文。双栏论文按阅读顺序重排，错序处标注。不合并跨章节内容，不漏段。若原文无显式标题，按内容边界划分并在 uncertainties 说明是推断划分。

### 第 3 步：字段化抽取
逐章逐段抽取笔记，每条包含：

- **field**：从字段字典选取，一条笔记只归一个主字段。
- **claim**：忠实转述的论断/数值/变量/方法条件，不添加原文外信息。
- **evidence**：支撑该 claim 的原文短引（15–40 词），必须能在 anchor 位置找到。
- **anchor**：原文位置，必须可回查。
- **confidence**：high / medium / low。

规则：数值、单位、变量符号、实验条件原样保留；因果/相关、限定词、否定关系不改变；一条论断多处分述时分条记录并各自给锚点。"作者自述的限制"和"可从方法推断的限制"要分开标 confidence，推断的不得写成作者主张。

### 第 4 步：术语与符号表
抽取关键术语、缩写、符号，记录统一写法与首次出现锚点。跨章节叫法不一致时统一 canonical 并保留原写法在 notes 中。

### 第 5 步：三重自检与回修（关键）
逐项核对 resources/checklist.md，并把结果写进 verification（带计数，不要只写"通过"）：

1. **字段覆盖计数**：逐项列出 research_question / motivation / method / dataset / metric / result / conclusion / limitation / reproduce_info 是否有笔记；原文未述的明确标注，不静默遗漏。
2. **锚点回查**：对每条笔记，按 anchor 回到原文，确认 evidence 短引与该位置一致；统计"回查成功数 / 总数"，任一失败必须修正或把 confidence 降为 low 并写入 uncertainties。
3. **事实一致**：数值、单位、变量、条件、限定词、因果、否定与原文逐条比对；发现被改写立即回第 3 步修正，记入 change_log。

章节完整：section 数量与原文标题数一致，无漏章漏段。

完成后 status 才能置 success；仍有未解决项则置 partial 并列出可人工接管位置。

### 第 6 步：输出结果
按结构写 `/app/output/result.json`，确认 case_id 已回填、字段齐全、verification 含计数、change_log 与 uncertainties 如实填写。

## 异常处理

| 情况 | 处理 |
|---|---|
| 扫描件 / 加密 / 权限受限 | 尝试 OCR；仍失败 status: unable 或 partial，说明具体页与原因 |
| 双栏错序 | 按阅读顺序重排，错序处写入 uncertainties |
| 图表公式缺失 | 保留占位与锚点，标注不可解析，不猜内容 |
| 超长文 | 分章处理，save early；标注处理到第几章 |
| 非中文论文 | 正常处理，笔记用中文，专有名词保留原文 |
| 字段原文未述 | 不臆造，写"原文未述"并计入 verification 覆盖统计 |

## 资源

- resources/checklist.md：自检清单（含计数模板）。
- resources/field_dict.md：字段字典、confidence 判定与锚点示例。
- resources/output_example.json：输出结构示意（非答案，字段完整）。
- examples/README.md：最小调用示例。

## 最小示例

见 examples/README.md。示意输出仅展示字段结构，不代表任何真实论文的笔记。
