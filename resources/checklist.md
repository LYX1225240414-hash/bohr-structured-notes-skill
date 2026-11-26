# 结构化笔记自检清单

自检结果要写进 result.json 的 verification 字段，**带具体计数**，不要只写"通过"。

## 章节完整
- [ ] section 数量 = 原文真实标题数（记录：原文 __ 节 / 输出 __ 节）
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
- [ ] anchor 格式符合 p<页>:<段> / <章节>:<段> / fig|tab|eq<号>
- [ ] 逐条回查 anchor 与 evidence 短引一致（回查成功 __ / 总数 __）
- [ ] 回查失败的条目已修正，或 confidence 降为 low 并写入 uncertainties
- [ ] 数值与变量的 evidence 短引与 anchor 位置一致

## 事实一致
- [ ] 数值、单位、变量、实验条件原样保留
- [ ] 因果/相关、限定词、否定关系未改变
- [ ] 未添加原文外信息；"作者主张"与"推断"已区分标注 confidence
- [ ] 术语跨章节统一，原写法保留在 notes

## 可核验性
- [ ] case_id 已从 case.json 原样回填
- [ ] status 与实际完成一致（success 必须全部自检通过；否则 partial + 可接管位置）
- [ ] sources 列出输入文件与页码范围
- [ ] 无法判断/材料缺失写入 uncertainties
- [ ] change_log 逐条记录自检回修：改动 / 原因 / 修正结果

## 诚实性红线
- 原文未述的字段不臆造、不补数值。
- 扫描件缺文字层不编造内容。
- 未核验的引用编号、图表指向不猜。
