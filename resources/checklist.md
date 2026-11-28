# 结构化笔记自检清单

自检结果要写进 result.json 的 verification 字段，**带具体计数**，不要只写"通过"。**能用脚本算的用脚本算，算不出的才人工填**。

| # | 项 | 口径 | 数据来源 |
|---|---|---|---|
| 1 | `section_alignment` | 原文节数 / 笔记节数 / 匹配数 / 套模板 / 漏章 / 顺序错 | `note_report.section_alignment` |
| 2 | `anchor_retrievability` | 锚点总数 / 无法解析 / 无法机械校验（需人工抽查） | `note_report.anchors` |
| 3 | `field_coverage` | 核心字段覆盖 / 9；无字段笔记条数 | `note_report.fields` |
| 4 | `evidence_fidelity` | 短引原文查不到条数，应为 0 | `note_report.evidence` |
| 5 | `numeric_fidelity` | 数值原文查不到数 / claim 数值不在 evidence 中数 | `note_report.numbers` |
| 6 | `consistency` | 重复笔记组数 / 同一对象多取值组数 | `note_report.duplicates`、`contradictions` |
| 7 | `reusability` | confidence 覆盖率 / tags 覆盖率 / 术语表条数 | `note_report.searchability` |
| 8 | `no_new_facts` | 新增原文没有的事实/数值/因果条数，应为 0 | `evidence.not_found` + 人工 |

## 章节完整
- [ ] `outline.json` 的 `section_count` 与笔记节数一致（原文 __ 节 / 输出 __ 节）
- [ ] `section_alignment.unmatched_count` 为 0：没有套用通用模板造出原文没有的章节
- [ ] `section_alignment.missing_count` 为 0：没有漏章
- [ ] `order_mismatch_count` 为 0：笔记章节顺序与原文论证顺序一致
- [ ] 无漏章漏段，双栏论文已按阅读顺序重排
- [ ] 每条笔记归属到正确章节

## 字段覆盖（逐项计数）
对下列每个字段，标记"有笔记 / 原文未述"，并统计覆盖数：

| 字段 | 有笔记? | 笔记条数 |
|---|---|---|
| research_question | | |
| motivation | | |
| method | | |
| dataset | | |
| metric | | |
| result | | |
| conclusion | | |
| limitation | | |
| reproduce_info | | |

覆盖计数：__ / 9。原文未述的字段已在笔记或 verification 中明确标注，不静默遗漏。

## 锚点可回链
- [ ] 每条笔记都有 anchor（缺 anchor 数：__）
- [ ] anchor 格式符合 `p<页>:<段>` / `sec:<章节名>[/p<段>]` / `fig|tab|eq<号>` / `line:<起>-<止>`
- [ ] `anchors.unresolved_count` 为 0：没有指向不存在的章节，也没有 `fig5` 而原文只有 2 张图这种越界
- [ ] `anchors.unverifiable` 条目已人工抽查（抽查 __ / 总数 __，附短引片段）
- [ ] 逐条回查 anchor 与 evidence 短引一致（回查成功 __ / 总数 __）
- [ ] 回查失败的条目已修正，或 confidence 降为 low 并写入 uncertainties

## 事实一致
- [ ] `evidence.not_found_count` 为 0：没有编造或拼接短引
- [ ] `numbers.orphan_count` 为 0：笔记数值都能在原文查到；换算已注明
- [ ] `numbers.claim_evidence_gap_count` 为 0：claim 的数值都在自身 evidence 里
- [ ] `duplicate_count` 为 0：没有重复条目
- [ ] `contradiction_count` 为 0：同一对象没有两个取值
- [ ] 数值、单位、变量、实验条件原样保留
- [ ] 因果/相关、限定词、否定关系未改变（人工）
- [ ] 未添加原文外信息；"作者主张"与"推断"已区分标注 confidence
- [ ] 术语跨章节统一（`glossary.missing_count` / `drift_count` 为 0），原写法保留在 notes

## 可核验性
- [ ] case_id 已从 case.json 原样回填
- [ ] status 与实际完成一致（success 必须全部自检通过；否则 partial + 可接管位置）
- [ ] `note_report` 数值与 `note_report.json` 一致（不是另算一套）
- [ ] 已生成 `index.md` / `index.json`，`reusability` 计数已填入
- [ ] sources 列出输入文件与页码范围
- [ ] 无法判断/材料缺失写入 uncertainties
- [ ] change_log 逐条记录自检回修：改动 / 原因 / 修正结果
- [ ] 包内无任何 `result.json`、无预制答案、无假造运行日志

## 诚实性红线
- 原文未述的字段不臆造、不补数值。
- 扫描件缺文字层不编造内容。
- 未核验的引用编号、图表指向不猜。
