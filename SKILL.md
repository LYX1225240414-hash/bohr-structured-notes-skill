---
name: structured-paper-notes
description: 把科研论文转化为章节对齐、字段齐备、逐条可回链的中文结构化笔记，并生成可检索索引；内置可离线运行的核验脚本（note_lint.py），从原文自动抽章节骨架（Markdown 标题 / 数字编号 / 中文编号 / 全大写节名，中英章节名走等价组），再把笔记与原文机械比对，检出套用通用模板的章节名、漏章、章节顺序颠倒、锚点指向不存在的章节或图号、evidence 短引在原文查不到（编造引文）、笔记数值在原文查不到、claim 数值与本条 evidence 不一致、重复笔记、术语统一写法未落实，并统计字段覆盖与可检索性；当用户要求读论文做笔记、提取研究问题/方法/数据/结果/结论/限制、生成可并排比较的文献卡片、或要求每条论断都能回到原文具体位置时使用，支持中英文期刊论文、会议论文与预印本。
---

# 文献总结与结构化笔记：章节对齐、字段齐备、锚点可回链

把真实论文变成**能继续用、能复核、能检索**的结构化笔记，而不是一段压缩后的通读摘要。核心是三层：**章节对齐 → 字段抽取 → 锚点回链**。每一条论断都要能回答两个问题："它来自原文哪里？"和"我怎么验证它没被改写？"

## 何时使用

- 读论文做笔记，要求按章节组织、字段化输出。
- 需要每条论断、数值、变量、方法条件都能回到原文具体位置。
- 需要覆盖研究问题、数据、方法、结果、结论、限制等完整要素。

不适用：无原文材料、仅要求一句话极简摘要、非科研文档。

## 运行环境与输出路径（重要）

- 平台把本 Skill 安装到 `/skills/weekly-skill`，用固定的 3 个案例运行。输入在 `/input/case.json`（含 `case_id` 与 `output_contract`）与同目录 `task.md`；原文按题目给出的材料路径读取，**不要用文件名或标签推断内容**。
- 工作文件放在 `/app/work`；**最终结果写到 `/app/output/result.json`**，可编辑产物也放 `/app/output`。
- 若输入是 PDF：用平台的 `pdf-text-tool` 抽文字层到 `/app/work/source.txt`；文字层缺失用 `ocr-tool`，仍失败则对应章节写入 `uncertainties` 并降级 `status: partial`。
- `result.json` 必须原样回填 `case_id`，并完整包含 `output_contract` 的全部字段（不得改名、不得遗漏）；本 Skill 定义的字段是最小集，合同字段更多时一并输出。
- 同时落盘：笔记主体 `/app/output/notes.json`（供脚本核验与复用）、可检索索引 `/app/output/index.md`、核验报告 `/app/output/note_report.md`。
- 预算内尽早写出诚实的部分结果再增量完善；3 个案例、每条件 3 次运行由平台安排，参赛者不提供测试案例或白板。
- 禁止提交预制答案、正式案例答案或假造运行日志；包内不应含任何 `result.json`。

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
| verification | 字符串键到对象的映射，逐项给 `result`（pass/fail/na）与 `evidence`（**带具体计数**）：`section_alignment`、`anchor_retrievability`、`field_coverage`、`evidence_fidelity`、`numeric_fidelity`、`consistency`、`reusability`、`no_new_facts` |
| note_report | 对象，原样转述 `note_report.json` 的关键计数，不得另算一套 |
| index | 对象，可检索性证据：按字段/章节/标签的条目分布（取自 `index.json`） |
| gain_record | 对象，含 `conditions` / `mode` / `baseline` / `with_skill` / `delta_note` / `verifiable_artifacts`；按 `resources/gain_protocol.md` 填写，无对照产出时写 `na` 并说明 |
| uncertainties | 无法判断、材料缺失、双栏错序、图表公式不可解析等条目及原因 |
| sources | 使用的输入文件/页码范围清单，便于复核输入边界 |
| change_log | 自检回修记录：每处改动、原因、修正后结果 |

**字段字典（notes.field）**：`research_question` / `motivation` / `method` / `dataset` / `metric` / `result` / `conclusion` / `limitation` / `reproduce_info` / `term`。

**锚点格式（anchor）**：`p<页>:<段号>` / `sec:<章节名>` 或 `sec:<章节名>/p<段号>` / `fig<号>` / `tab<号>` / `eq<号>` / `line:<起>-<止>`，必须指向原文真实位置。`sec:` 后的章节名要与原文标题一致（英文论文写 `sec:Introduction`，中文论文写 `sec:引言`，脚本按中英等价组识别）。

## 工作流

### 第 1 步：读取输入边界
读取实际文件，不用文件名或标签推断内容。确认页数、语言、单双栏、是否有图表公式、是否扫描件。缺文件 → status: unable 并说明缺什么。扫描件尝试 OCR，失败写入 uncertainties。把输入清单记入 sources。

### 第 2 步：章节对齐（先让脚本抽骨架）

```bash
L=/skills/weekly-skill/resources/scripts/note_lint.py
python3 "$L" outline --source /app/work/source.txt --out /app/work
```

`outline` 输出 `outline.json`：从原文识别 4 类章节标记（Markdown `#` 标题、`1. Methods` 数字编号、`一、引言` 中文编号、`INTRODUCTION` 全大写节名），并给出 `paragraph_count` / `page_count` / `max_fig` / `max_tab` / `max_eq` 四个用于校验锚点的边界值。

**以 `outline.json` 的章节列表为骨架切分笔记，不要用通用模板**。原文没有的章节不要凭空造；原文是中文标题就沿用中文标题（脚本按中英等价组识别 `Introduction`↔`引言`，但凭空多出一个 `Discussion` 会被判为套模板）。双栏论文按阅读顺序重排，错序处标注。若原文无显式标题，按内容边界划分并在 `uncertainties` 说明是推断划分。

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

### 第 5 步：机械核验与回修（关键）

**先跑脚本，再人工判读**——"引文是编的""锚点指的图不存在""章节套了模板"这三类事故靠通读几乎查不出来：

```bash
python3 "$L" check --source /app/work/source.txt \
                   --notes /app/output/notes.json --out /app/output
```

产物：`/app/output/note_report.json`（机读）、`/app/output/note_report.md`（人读，按类别分组）。逐类处置：

| 类别 | 含义 | 必须动作 |
|---|---|---|
| `section_alignment.unmatched` | 笔记章节名在原文找不到等价章节 | **改用原文真实章节名**；原文确实没有该节就删掉，不要空着占位 |
| `section_alignment.missing_from_notes` | 原文有、笔记没有的章节 | 补该章节笔记；确无内容则写"原文该节仅有 X"并给锚点 |
| `section_alignment.order_mismatch` | 笔记章节顺序与原文相反 | 按原文顺序重排——笔记骨架要反映原文论证顺序 |
| `anchors.unresolved` | 锚点指向不存在的章节/超出原文最大图号表号 | **改成真实位置**；`fig5` 但原文只有 2 张图，说明锚点是猜的 |
| `anchors.unverifiable` | 原文无分页符等，无法机械校验 | 人工抽查，`verification` 里写清抽查数与片段 |
| `evidence.not_found` | evidence 短引在原文查不到 | **最严重的一类**：把原文原句复制回来；找不到就说明该论断无原文支撑，必须删改 |
| `numbers.orphan` | 笔记里的数值在原文查不到 | 核对是否换算/改写/编造；换算要注明换算方式 |
| `numbers.claim_evidence_gap` | claim 的数值不在本条 evidence 中 | 确认该数值来自哪个锚点；定位不到就改写或把 confidence 降为 low |
| `duplicates` | 同一字段的两条笔记几乎相同 | 合并并保留多锚点，避免条目膨胀、互相矛盾 |
| `contradictions` | 同一对象在笔记中出现多个取值 | 核对哪一处对得上原文，另一处改正或说明条件差异 |
| `glossary.missing` / `glossary.drift` | 术语 canonical 未用 / 多种写法 | 统一为 canonical 并回扫全文 |
| `fields.missing` / `notes_without_field` | 字段缺口 / 笔记没填 field | 补齐；原文确实未述则写"原文未述"并记入 `uncertainties` |

修完重跑 `check`，直到 `anchors.unresolved`、`evidence.not_found`、`numbers.orphan`、`numbers.claim_evidence_gap`、`duplicates` 全部为 0，或每条残留都在 `uncertainties` 有明确理由。每轮回修写入 `change_log`。

脚本测不出、必须人工判断的部分（写进 `verification` 的 `no_new_facts` 与 `uncertainties`）：转述是否忠实（没有把"相关"写成"因果"）、限制条件是作者自述还是你推断的、图表内部信息是否被误读。**脚本给 0 差异不等于笔记写对了，只等于没编引文、没抄错数、没指错位置。**

### 第 5.5 步：生成可检索索引（用得上）

```bash
python3 "$L" index --notes /app/output/notes.json --out /app/output
```

产出 `index.md`（按字段 / 章节 / 标签三张表 + 条目清单）与 `index.json`。索引是"笔记可继续加工"的证据：多篇论文的 `index.json` 按字段并排在一起就能做跨文献比较。把 `index.json` 的分布写进 `result.json` 的 `index` 字段。

### 第 6 步：自检与输出

逐项核对 `resources/checklist.md`，**优先采用 `note_report.json` 的机械计数**，只有脚本测不出的项才人工计数：
1. **字段覆盖**：取 `fields.covered_count / 9`，原文未述的字段单独列出，不静默遗漏。
2. **锚点回查**：取 `anchors` 三类计数；`unverifiable` 的做人工抽查并记录短片片段。
3. **事实一致**：取 `evidence.not_found` 与 `numbers.*` 计数；因果、限定、否定的改写需人工判断。

写 `/app/output/result.json`，确认 `case_id` 已回填、`output_contract` 字段齐全、`verification` 每项带计数、`note_report` 与 `note_report.json` 一致。完成后 `status` 才能置 `success`；仍有未解决项则置 `partial` 并列出可人工接管位置。

### 第 6.5 步：增益记录（使用增益 25 分）

按 `resources/gain_protocol.md` 记录对照条件、指标与可复算产物，写入 `result.json` 的 `gain_record`。无外部白板时用"同一运行内两版笔记"方式：先按"通读一遍直接写笔记"产出 `notes_blind.json`，再按本工作流产出定稿，两版**对照同一份原文**分别跑 `check`，比较章节对齐、锚点解析、短引查得率与数值保真计数的变化。**不得编造对照数据**，测不出就写 `na` 并说明原因。

## 异常处理

| 情况 | 处理 |
|---|---|
| 扫描件 / 加密 / 权限受限 | 尝试 OCR；仍失败 status: unable 或 partial，说明具体页与原因 |
| 双栏错序 | 按阅读顺序重排，错序处写入 uncertainties |
| 图表公式缺失 | 保留占位与锚点，标注不可解析，不猜内容 |
| 超长文 | 分章处理，save early；标注处理到第几章 |
| 非中文论文 | 正常处理，笔记用中文，专有名词保留原文 |
| 字段原文未述 | 不臆造，写"原文未述"并计入 verification 覆盖统计 |
| 原文无显式章节标题 | `outline.json` 的 `section_count` 会偏低；按内容边界划分并标 `kind: inferred`，写入 `uncertainties` |
| `notes.json` 无法解析 | 检查是否漏写 `sections[].notes` 或 `notes` 顶层数组；脚本对两种结构都支持，但键名必须是这两者之一 |
| 脚本报原文为空 | PDF 未抽文字层是最常见原因，先用 `pdf-text-tool` 落 `/app/work/source.txt` |

## 资源

- `resources/scripts/note_lint.py`：**执行内核**。`outline` 抽原文章节骨架并给出锚点校验边界（段落数/页数/最大图号表号公式号）、`check` 做章节对齐 + 锚点可回查 + 字段覆盖 + 短引保真 + 数值保真 + 重复矛盾 + 术语 + 可检索性八类核验、`index` 生成可检索索引。纯标准库（`argparse`/`re`/`json`/`difflib`/`collections`/`pathlib`），无第三方依赖，可完全离线运行。
- `resources/checklist.md`：自检清单（含计数模板）。
- `resources/field_dict.md`：字段字典、confidence 判定与锚点示例。
- `resources/gain_protocol.md`：使用增益对照协议与 `gain_record` 记录格式。
- `resources/output_example.json`：输出结构示意（非答案，字段完整）。
- `environment/resources.yaml`：资源清单、依赖、运行时与产物说明。
- `examples/README.md`：最小调用示例（含真实实测输出，非虚构）。

## 最小示例（示意，非真实论文）

```bash
L=/skills/weekly-skill/resources/scripts/note_lint.py

# 1) 抽原文骨架，拿到真实章节名与 max_fig / max_tab（锚点校验边界）
python3 "$L" outline --source /app/work/source.txt --out /app/work

# 2) 按骨架写 /app/output/notes.json 后核验
python3 "$L" check --source /app/work/source.txt \
                   --notes /app/output/notes.json --out /app/output

# 3) 生成可检索索引
python3 "$L" index --notes /app/output/notes.json --out /app/output
```

示意输出（仅结构与计数口径，数值为占位）：

```json
{"sections": {"source": 6, "notes": 5, "unmatched": 0, "missing": 0},
 "anchors": {"total": 12, "unresolved": 0, "unverifiable": 0},
 "fields_covered": "8/9", "evidence_not_found": 0,
 "number_orphan": 0, "duplicates": 0, "contradictions": 0, "glossary_missing": 0}
```

真正的结果必须来自本次实际运行，示意输出不得冒充正式案例答案。
