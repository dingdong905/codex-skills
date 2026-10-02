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


## dingdong905/design-skills / Stramony/design-skills

- 集合：https://github.com/dingdong905/design-skills；父仓库：https://github.com/Stramony/design-skills。
- 固定提交：`552a823c376b7e05dae51b625332b550dab4ef69`，本批仅选择 `ui-ux-pro-max`、`brand` 与 `design-system` 的 Token 部分。
- 上游 brand/design-system 元数据作者为 claudekit。ui-ux-pro-max 原作者与组件许可未由该快照明确说明，保留来源而不虚构归属。
- 集合不提供统一许可。design-system SKILL.md 声明 MIT；brand/ui-ux-pro-max 未见组件级许可文件或入口声明，须在公开再分发前补齐授权。新增技能不自动适用本仓库 MIT 声明。
- 字体与图标数据保留 `data-provenance.json`、`google-font-licenses.json`、`phosphor-icons-upstream.json` 和快照记录，引用资源仍受各自条款约束。
- 改动：精简中文入口、修复平台路径、取消缺失的 SwiftUI stack、保留品牌与状态语义、只同步明确色值、生成主题变量引用及补充离线回归。
- 各技能 SOURCE.json 随安装携带来源、许可状态和修改范围，详见 [设计技能集成说明](docs/design-skills-integration.md)。


### 第二批选择性适配

- 同一提交 `552a823c376b7e05dae51b625332b550dab4ef69` 的 `hallmark`、`banner-design` 和 `ui-styling`。
- Hallmark 保留视觉层级、具体性、结构差异和参考分析思想；重写入口和模式资料，取消强制换主题、审美禁令、自动日志和自评分印章。快照没有明确组件级许可。
- banner-design 上游入口声明 MIT；改用内置 imagegen、可编辑合成和只读 PNG 检查，取消 Gemini 与缺失工具依赖。尺寸资料加上平台时效与印刷边界。
- ui-styling 上游 metadata 作者为 claudekit。入口声明 MIT，随附 LICENSE.txt 却为 Apache-2.0；保留该文件和冲突记录，不声称已确定唯一适用许可。仅适配 React/shadcn/Tailwind 实现思想，未导入 Canvas/海报内容或 CLI 包装脚本。
- 三个技能 SOURCE.json 随安装保留来源和修改范围。许可证归属未明确的组件不会自动套用本仓库 MIT。


### 第三批拆分与资料整合

- 同一快照的 design/logo 与 design/cip 数据分别进入 logo-design 和 brand-collateral；保留 claudekit attribution 和上游 design 入口的 MIT 声明，集合不提供新的统一许可。
- 七份 CSV 保持原样；重写标准库检索入口，保留 BM25 排序思想，增加明确域、结果上限和规范名称优先。Gemini 生成、环境文件读取和硬编码 HTML 渲染脚本未导入。
- design/icon 与 social-photos 的适用规则分别提取到新技能参考资料，不创建重复的全能 design 入口。
- slides 叙事/布局及 design-system 的图表思想按任务提取到现有 pitch-deck、data-report-deck、technical-explainer-deck。slides 快照没有明确组件许可，单独记录在这些技能 references/design-skills-source.json，公开再分发前需明确授权；不会因整合到已有技能就套用它们的许可声明。

## vercel-labs/skills — find-skills

- 来源：https://github.com/vercel-labs/skills，固定提交 3694740352eeef5cdd689af694c485f1ff62eec3，路径 skills/find-skills/SKILL.md。
- MIT，Copyright (c) 2026 Vercel, Inc.；许可原文保存在 find-skills/LICENSE.txt。
- 适配为中文精简入口，收紧触发、补充源码/许可/重叠检查、来源记录、上下文预算及隔离验证；未导入 CLI 源码或依赖。
