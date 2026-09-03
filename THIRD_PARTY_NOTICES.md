# 第三方来源与许可说明

本仓库对若干开源技能进行了中文本地化、Codex 适配或工作流重构。上游内容的版权归原作者所有。

## ustc-ai4science/academic-search

- 项目：https://github.com/ustc-ai4science/academic-search
- 许可证：MIT
- 相关技能：`academic-search`
- 上游版本：`1.2.0`，适配基线提交 `3ae68445`
- 改动：压缩 Codex 入口、替换 Claude/CDP 专属假设、强化撤稿与版本核验、跨学科证据评价，以及研究证据到生活判断的转化边界。

## affaan-m/ECC

- 项目：https://github.com/affaan-m/ECC
- 许可证：MIT
- 相关技能：`context-budget`、`evidence-research`
- 改动：面向 Codex 重构触发范围、检索流程、上下文预算和中文入口。

## alirezarezvani/claude-skills

- 项目：https://github.com/alirezarezvani/claude-skills
- 许可证：MIT
- 相关技能：`financial-analyst`、`memory-curator`、`research-summarizer`、`stock-analysis`
- 改动：中文入口与界面元数据、Codex 适配、技能边界调整，以及部分工作流强化。

上游 MIT License 可在对应项目中查看。仓库内 `references/SKILL.en.md` 是为回滚和升级对照保留的英文入口备份，并不表示上游仓库的完整镜像。
