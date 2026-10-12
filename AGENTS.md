# Skill 仓库治理

创建或更新 Skill 时先改 D:\skills 下目标平台源仓库：Codex 用 D:\skills\codex-skills，WorkBuddy 用 D:\skills\workbuddy-skills；用户指定其他位置时遵从。需要本机调用再安装运行时目录。

- SKILL.md / references/ 保留可复用的规则、决策、执行契约；具体项目、设备、本机环境、完整演示、填好的产物与复盘统一放各 Skill 的 example/（单数）。
- 精确 API 字段、通用算法、参数化脚本和空白模板留在适当资源目录；tests/、evals/ 专用 fixture 保持测试用途。
- 案例同步 example/index.json：场景、前提、预期/实测结果、边界、来源与原核验日期。案例不作为默认事实或新授权。
- 所有 AI 新建、修改、导入、迁移 Skill 遵循 docs/skill-governance.md；生成前分层，交付前运行 python -B scripts/lint_skill_governance.py，复核语义与受影响功能。
- 保留平台原生 frontmatter、调用策略、来源许可与用户已有变更。实际任务进度先存用户项目，不自动回写 Skill。

2026-10-08 用户已批准并执行两份迁移清单。新增、修改、导入或迁移 Skill 后运行 python -B scripts/lint_skill_governance.py 全量严格检查；单独审查可加 --skill <skill-name>。不得刷新基线规避分层要求。
