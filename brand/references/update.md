# 更新品牌与 Token

在用户授权的品牌更新范围内修改指南。项目原有路径优先；默认是 `docs/brand-guidelines.md`。以实际品牌事实为准，不使用模板或上游示例替换项目品牌名称。

## 可解析输入

颜色采用六位 hex。脚本接受 Quick Reference 行 `| Primary Color | #2563EB |`（以及 Secondary/Accent），或 `### Primary Colors`、`### Secondary Colors`、`### Accent Colors` 下的表格。行名含 Dark 或 Light 时映射到显式色阶；Secondary 表中的 Accent 行只作为 Accent，不抢占 Secondary base。Quick Reference 与表格基础色冲突时停止，让用户或维护者明确一个值。

脚本只同步提供的 swatch：基础色到 `primitive.color.<role>.500`，明确 Dark 到 600，明确 Light 到 100；语义角色通过别名指向这些值。已有项目必须检查这一角色命名是否合适；若已有映射不同，应手工编辑 JSON，而不是运行通用同步器。

## 执行

从任何工作目录执行 `SKILL.md` 中带绝对脚本路径及 `--project-root` 的命令。非默认文件位置使用项目内的 `--guidelines`、`--tokens`、`--css`，可相对项目根或用绝对路径。输出预览 `--dry-run` 不写文件。

同一技能安装根下应有 `design-system/scripts/generate-tokens.cjs`；可通过 `--generator` 显式指定。先验证完整配置、引用和 CSS 生成，再写 JSON/CSS；缺失生成器、无可解析颜色或非法 Token 会返回失败且不写输出。

保留状态颜色（success/error/info/destructive）、项目名称、未涉及的原始色阶及其他 Token。同步不产生推导色阶；已有衍生色阶不会自动更新，因此仍需人工审查所有 hover/active 和暗色主题组合。缺少前景或对比数据时报告缺口，不声称符合可访问性标准。
