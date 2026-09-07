# 第三方来源与许可说明

本仓库对若干开源技能进行了中文本地化、Codex 适配或工作流重构。上游内容的版权归原作者所有。

## ustc-ai4science/academic-search

- 项目：https://github.com/ustc-ai4science/academic-search
- 许可证：MIT
- 相关技能：`academic-search`、`ai-computing-research`、`biomedical-evidence`
- 上游版本：`1.2.0`，适配基线提交 `3ae68445`
- 改动：压缩 Codex 入口、替换 Claude/CDP 专属假设、强化撤稿与版本核验、跨学科证据评价，以及研究证据到生活判断的转化边界。

## google-deepmind/science-skills

- 项目：https://github.com/google-deepmind/science-skills
- 许可证：Apache-2.0
- 相关技能：`biomedical-evidence`、`research-toolkit`
- 参考模块：PubMed、ClinicalTrials.gov 与 Europe PMC 数据库技能
- 改动：未复制其脚本；借鉴 grounding、限流、字段裁剪、试验注册和开放全文边界，使用 Python 标准库重新实现统一接口。

## xwmxcz/papers-skill

- 项目：https://github.com/xwmxcz/papers-skill
- 许可证：MIT
- 相关技能：`ai-computing-research`、`research-toolkit`
- 改动：借鉴 Semantic Scholar/arXiv 的轻量 CLI 与先元数据后全文流程；未复制依赖型脚本，改为多数据源统一证据契约。

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

## Akxan/ppt-agent-skill

- 项目：https://github.com/Akxan/ppt-agent-skill
- 许可证：MIT
- 相关技能：`technical-explainer-deck`、`deck-review`
- 改动：借鉴认知负荷、叙事结构、视觉层级、数据表达和常见失败模式；没有复制其 HTML/PptxGenJS 生成链路、模板库或视觉 QA 脚本。

## CacinieP/ppt-skills

- 项目：https://github.com/CacinieP/ppt-skills
- 许可证：MIT
- 相关技能：`technical-explainer-deck`、`deck-review`
- 改动：借鉴中文字体、CJK 文本溢出、WCAG 对比度、可编辑性检查和版式契约思路；当前静态审计脚本为独立实现，没有复制上游脚本。

## algerchen2024/image-to-editable-pptx

- 项目：https://github.com/algerchen2024/image-to-editable-pptx
- 许可证：MIT
- 相关文档：`docs/presentation-stack-architecture.md`
- 改动：将“截图或扫描页还原为可编辑 PPTX”识别为未来独立品类；当前未复制其 PageIR、脚本或示例资产。

PPT 栈还评估了 `presenton/presenton`（Apache-2.0）和 `gitbrent/PptxGenJS`（MIT），但当前不新增其代码依赖。`anthropics/skills` 的 PPTX Skill 使用专有许可并禁止复制或创建衍生作品，本仓库未复用其内容。
