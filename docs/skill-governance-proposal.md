# 已批准的案例迁移记录

2026-10-08 用户批准后，本清单对应补丁已执行；相邻 .patch 保留为审阅记录，不应重复应用。

影响 58 个文件路径。移动保留内容，同步引用并登记 example/index.json。

## 迁移项

- stock-analysis/examples/forensic-analysis-example.md → stock-analysis/example/forensic-analysis-example.md
- stock-analysis/examples/README.md → stock-analysis/example/README.md
- stock-analysis/examples/standard-analysis-example.md → stock-analysis/example/standard-analysis-example.md
- evidence-driven-valuation/examples/synthetic-handoff.json → evidence-driven-valuation/example/synthetic-handoff.json
- tech-mentor/references/topics/metallb.md → tech-mentor/example/topics/metallb.md
- android-phone-ops/references/xiaomi14-jev-v13.md → android-phone-ops/example/xiaomi14-jev-v13.md
- android-phone-ops/references/tara-social.md → android-phone-ops/example/tara-social.md
- financial-analyst/assets/sample_financial_data.json → financial-analyst/example/sample_financial_data.json
- academic-search/references/routing.md#边界案例 → academic-search/example/routing-boundaries.md
- ui-ux-pro-max/references/ui-guidance.md#Example Workflow → ui-ux-pro-max/example/workflow.md
- brand/references/asset-organization.md#Examples → brand/example/asset-names.md
- brand/references/color-palette-management.md#Color Palette Examples → brand/example/color-palettes.md
- brand/references/logo-usage-rules.md#Visual Examples → brand/example/logo-misuse.md
- design-system/references/component-tokens.md#Usage Example → design-system/example/component-usage.md
- design-system/references/tailwind-integration.md#Button Example → design-system/example/tailwind-button.md
- stock-analysis/references/11-scoring-rubric.md#11. Worked example A — the lower-margin company scores higher → stock-analysis/example/scoring-sector-comparison.md
- stock-analysis/references/11-scoring-rubric.md#12. Worked example B — a gate overrides a strong scorecard → stock-analysis/example/scoring-gates.md
- stock-analysis/references/11-scoring-rubric.md#13. Worked example C — renormalisation when data is missing → stock-analysis/example/scoring-missing-data.md

## 需语义审阅的修改

- 教学样例与当前用户学习状态分开，当前进度留用户项目。
- 财务工具通用调用使用输入与参数占位符，合成输入放 example/。
- 来源许可、平台元数据保留；迁移不声称重新实测。

## 验证与备份

迁移后执行全量严格治理检查、受影响功能检查和 git diff --check。备份保存了源文件和已有未提交变更：D:/skills/audit-backups/skill-governance-approved-20261008-e5cfb637。

## 补充迁移

用户单独批准的两项收尾迁移已执行，见 [补充记录](skill-governance-supplement.md)。财务示意输出与估值历史审计已归入 example/，通用限制保留在 references/known-limitations.md。
