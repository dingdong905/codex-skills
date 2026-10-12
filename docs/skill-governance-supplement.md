# 已批准的两项补充迁移

2026-10-08 用户单独批准后，以下两项补充迁移已执行。相邻补丁保留为审阅记录，不应重复应用；补充迁移前状态已另存 supplement-before.zip。

1. financial-analyst/assets/expected_output.json → financial-analyst/example/expected_output.json。原文件明确是填好示意值的输出演示，保持 JSON 内容不变，登记 index.json。
2. evidence-driven-valuation/references/audit-notes.md → evidence-driven-valuation/example/audit-notes.md。原记录描述具体日期、本机备份、修复与算例；保留原文，将其中通用的已知限制原样摘到 references/known-limitations.md，更新入口链接并登记 index.json。

不修改计算器、公式、测试语义或平台元数据。执行后进行严格检查与关联验证。迁移前原文件已在此前完整备份中。
