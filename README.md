# 文献总结与结构化笔记 Skill（对得上 · 留得住 · 找得回 · 用得上）

玻尔科学空间高校挑战赛 · 北京化工大学分站赛 —— 阅读10｜文献总结与结构化笔记 赛题作品。

## 简介

把真实论文变成**章节对齐、字段齐备、逐条可回链、可继续加工**的结构化笔记，而不是一段压缩后的通读摘要。

两条核心设计：

1. **骨架来自原文，不来自模板**——先用 `note_lint.py outline` 抽出原文真实章节（Markdown 标题 / `1. Methods` 数字编号 / `一、引言` 中文编号 / 全大写节名），再按骨架切分；原文没有 `Discussion` 就不许凭空写出 `Discussion`。
2. **回链靠机械核验**——evidence 短引是否真在原文、锚点是否指向存在的章节与图号、笔记数值是否原文查得到、claim 的数值是否就在自己的 evidence 里，全部可计数，而不是靠通读感觉。

## 目录结构

```
SKILL.md                           Skill 定义（YAML frontmatter + 8 步工作流 + 运行契约）
environment/resources.yaml         资源清单、依赖、运行时与产物说明
resources/scripts/note_lint.py     执行内核：outline / check / index（纯标准库，可离线）
resources/field_dict.md            字段字典、锚点三态、notes.json 结构与 claim/evidence 硬规则
resources/gain_protocol.md         使用增益对照协议与 gain_record 记录格式
resources/checklist.md             带计数口径的自检清单（对应 verification 八项）
resources/output_example.json      输出结构示意（非答案）
examples/README.md                 最小调用示例（含真实实测输出，非虚构）
```

## 执行内核 `note_lint.py`

三个子命令，纯标准库（`argparse`/`re`/`json`/`difflib`/`collections`/`pathlib`），无第三方依赖：

| 子命令 | 作用 |
|---|---|
| `outline` | 抽原文章节骨架；同时给出 `paragraph_count` / `page_count` / `max_fig` / `max_tab` / `max_eq`，这些是锚点校验的边界值 |
| `check` | 笔记 vs 原文，八类核验（见下） |
| `index` | 生成 `index.md` + `index.json` 可检索索引（按字段 / 章节 / 标签） |

`check` 的八类检查：

| 类别 | 具体项 |
|---|---|
| 章节对齐 | 套模板章节（`unmatched`）、漏章（`missing`）、顺序颠倒（`order_mismatch`） |
| 锚点可回查 | `unresolved`（指向不存在的章节、`fig5` 超出原文最大图号）、`unverifiable`（原文无分页符，需人工抽查） |
| 字段覆盖 | 9 个核心字段的覆盖 / 缺口 / 未填 field 的笔记数 |
| 短引保真 | evidence 去空白去标点后是否真能在原文找到（编造引文的核心检测） |
| 数值保真 | 笔记数值是否原文查得到；claim 数值是否就在本条 evidence 中 |
| 一致性 | 同字段重复笔记、同一对象多取值 |
| 术语 | canonical 未落实 / 多种写法 |
| 可检索性 | confidence 覆盖率、tags 覆盖率、字段分布 |

工程上有四处刻意设计，避免"脚本乱报带着人改坏笔记"：

- **中英章节名等价组**：原文 `Introduction`、笔记写"引言"不算套模板；但原文没有 `Discussion` 而笔记写了，会被判套模板——这两种情况必须区分开。
- **锚点分三态**：`ok` / `unresolved`（必须改）/ `unverifiable`（只能人工抽查）。把"查不了"和"查到了不对"混成一类会让所有锚点告警失去意义。
- **数值两层**：`orphan`（原文查不到，硬错误）与 `claim_evidence_gap`（claim 有、自己的 evidence 没有，需核对来源），强度不同，处置不同。
- **去空白去标点后比对短引**：论文文字层常有换行与全半角差异，直接子串匹配会大量误报"查不到"。

## 使用方式

在支持 Skill 的 Agent 环境中加载本目录，把论文（PDF / TXT / MD）与任务要求交给 Agent。Agent 按 SKILL.md 的工作流执行：

落盘骨架 → 读输入边界 → `outline` 抽骨架并章节对齐 → 字段化抽取 → 术语表 → `check` 核验并回修 → `index` 生成索引 → 增益记录 → 自检与输出。

## 输出约定

`/app/output/result.json` 原样回填 `case_id`、完整包含 `output_contract` 全部字段，并提供 `paper_meta`、`sections`、`glossary`、`verification`（八项带计数）、`note_report`（转述 `note_report.json`）、`index`（可检索性分布）、`gain_record`、`uncertainties`、`sources`、`change_log`。同时落盘笔记主体 `notes.json`、核验报告 `note_report.md` 与索引 `index.md`。

## 版本

- v1.1.0：接入 `note_lint.py` 执行内核；新增 `environment/resources.yaml`、`gain_protocol.md`；`field_dict` 补锚点三态与 `notes.json` 结构；`checklist` 补计数口径表。
- v1.0.0：章节对齐 + 字段化抽取 + 三重自检的纯文档版工作流。

## 授权

仅供赛事评审与学习交流使用。
