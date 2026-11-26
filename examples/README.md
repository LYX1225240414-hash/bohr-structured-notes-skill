# 最小调用示例（示意）

以下仅为字段结构演示，不是正式案例答案，也不是任何真实论文的笔记。

## 输入

```text
请为下面这篇论文生成结构化笔记：按章节对齐，抽取研究问题/方法/数据/结果/结论/限制，每条笔记给出原文锚点。
[此处粘贴论文文本或给出文件路径]
```

## 调用方式

在 Agent 中加载本 Skill，把上述输入发给 Agent。Agent 按 SKILL.md 的 6 步执行：读输入边界 → 章节对齐 → 字段化抽取 → 术语表 → 三重自检回修 → 输出。运行结果写到 `/app/output/result.json`（本地演示时写到本地输出目录），case_id 从输入的 case.json 原样回填。

## 示意输出

见 ../resources/output_example.json：sections 按章节组织，每条 note 含 field/claim/evidence/anchor/confidence，术语进 glossary，自检进 verification。

## 说明

- 示意输出仅展示结构，不代表任何真实论文的笔记质量。
- 真实评测由平台用固定的 3 个案例运行，参赛者不提供测试案例或白板。
