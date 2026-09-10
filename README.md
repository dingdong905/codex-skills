# Codex Skills 中文增强集

面向中文用户维护的个人 Codex Skills 仓库，重点增强：

- 多来源信息检索、证据分级与交叉核验
- 上市公司基本面、财报洞察与财务取证
- 研究材料摘要、比较与信息整合
- Codex 上下文治理与 Token 节省
- 长期记忆整理、冲突处理与过期管理
- 按演示目的细分的 PPT 研究、叙事、构建与质量评测

技能调用名保持英文，正文和界面说明采用中文；必要的英文关键词会保留，以兼容中英文自动触发。

## 与 WorkBuddy 的双轨维护

Codex 与 WorkBuddy 各自维护完整、原生兼容的一套 Skill，不通过软链接或运行时共享文件去重。成熟的工作流、参考资料、脚本思路和评测案例可以择优双向迁移，但元数据、工具名、权限模型、调用策略和验证命令必须按目标平台重新适配。详细约定见 [docs/cross-platform-maintenance.md](docs/cross-platform-maintenance.md)。

## 技能目录

| 技能 | 用途 | 示例调用 |
| --- | --- | --- |
| `academic-search` | 薄编排器：为模糊/跨学科问题选择专业 Skill | `使用 $academic-search 研究 AI 医疗的算法与临床证据` |
| `ai-computing-research` | AI/计算机前沿、版本、benchmark 与复现审计 | `使用 $ai-computing-research 找近半年 LLM 推理研究` |
| `biomedical-evidence` | 医学指南、综述、试验、绝对风险与安全边界 | `使用 $biomedical-evidence 评估改善睡眠的证据` |
| `research-toolkit` | 共享检索、规范化、去重和标识符核验工具层 | `使用 $research-toolkit 核验这些 DOI 和 PMID` |
| `evidence-research` | 当前、多来源、可审计的信息研究 | `使用 $evidence-research 调查……` |
| `stock-analysis` | 上市公司基本面、A 股披露、估值和财务取证 | `使用 $stock-analysis 分析腾讯最新财报` |
| `financial-analyst` | 财务比率、DCF、预算差异与预测 | `使用 $financial-analyst 建立 DCF` |
| `research-summarizer` | 已提供论文、报告和网页的结构化摘要 | `使用 $research-summarizer 比较这些报告` |
| `context-budget` | 审计上下文膨胀并减少 Token 消耗 | `使用 $context-budget 审计当前配置` |
| `memory-curator` | 管理 Codex 记忆、项目约定和任务交接 | `使用 $memory-curator 整理长期记忆` |
| `tech-mentor` | 显式启动的系统学习、练习与掌握检验 | `使用 $tech-mentor 系统学习 MetalLB` |
| `presentation-studio` | 薄编排器：形成 brief 并路由 PPT 品类 | `使用 $presentation-studio 规划这份汇报` |
| `technical-explainer-deck` | 精细技术体系、架构、机制、参数和选型演示 | `使用 $technical-explainer-deck 做 AI Infra 技术培训` |
| `executive-decision-deck` | 管理层审批、方案比较和资源决策 | `使用 $executive-decision-deck 做立项汇报` |
| `research-presentation` | 论文、实验、组会与学术会议汇报 | `使用 $research-presentation 做论文汇报` |
| `pitch-deck` | 创业项目和融资路演 | `使用 $pitch-deck 做种子轮 BP` |
| `data-report-deck` | KPI、经营复盘和数据故事 | `使用 $data-report-deck 做季度复盘` |
| `teaching-deck` | 课程、工作坊、示例和练习型课件 | `使用 $teaching-deck 做课堂课件` |
| `deck-review` | PPT 内容、证据、视觉和可编辑性 QA | `使用 $deck-review 审阅并修复这份 PPT` |

## PPT 混合架构

PPT 能力采用“专业品类 Skill + 统一执行层 + 薄编排器 + 评测体系”：

    presentation-studio（brief 与路由）
    ├─ technical-explainer-deck（精细样板）
    ├─ executive-decision-deck
    ├─ research-presentation
    ├─ pitch-deck
    ├─ data-report-deck
    └─ teaching-deck

    Presentations（Codex 现有 PPTX 构建、模板、渲染）
    deck-review（独立质量门）
    evals/presentation-stack（路由、质量、硬失败与 Token 预算）

先根据两份技术演示样例把“企业内部技术体系讲解、技术选型与培训”做精细，其余品类提供轻量但可用的基线。样例中的品牌、内部内容和原始 PPTX 不进入公开仓库。完整设计和开源取舍见 [docs/presentation-stack-architecture.md](docs/presentation-stack-architecture.md)。

离线校验：

    python evals/presentation-stack/score_eval.py lint
    python deck-review/scripts/deck_audit.py example.pptx --mode live --json

## 学习导师

`tech-mentor` 只接受显式调用，不会因普通“解释一下”自动注入上下文。它从 WorkBuddy 版本迁移了预测—尝试—反馈—检验、失败降级、间隔与交错练习等有效机制，同时按 Codex 的授权和持久化边界重新实现。

离线校验：

    python -m unittest discover -s tech-mentor/tests -v
    python evals/tech-mentor/score_eval.py lint
    python tech-mentor/scripts/validate_topic.py tech-mentor/references/topics/metallb.md

## A 股研究分支

`stock-analysis` 对沪深北 A 股按需加载专属披露规则，并在通用数据门之上检查审计、扣非、资金占用、质押冻结、监管措施、研发资本化和重组/商誉底稿。其他市场不会加载该 reference。

离线校验：

    python -m unittest discover -s stock-analysis/tests -v
    python stock-analysis/evals/lint_evals.py
    python stock-analysis/scripts/verify_a_share.py --template

## 论文研究混合架构

论文研究采用“专业 Skill + 统一工具层 + 薄编排器 + 评测体系”：

    academic-search（只路由与跨域合并）
    ├─ ai-computing-research
    ├─ biomedical-evidence
    └─ 后续领域 Skill

    research-toolkit（共享 API、规范化、去重、标识符核验）
    evals/research-stack（路由、引用、领域质量、安全与 Token 预算）

明确的 AI/计算机或医学问题会直接使用专业 Skill，避免加载跨学科入口的全部规则。当前先用差异最大的两个领域验证架构；历史、地理、天文、社会学和哲学暂由 academic-search 明示“通用回退”，评测达标后再逐个加入。

统一工具层只处理稳定的数据操作，专业 Skill 负责领域判断。这样可以独立替换数据源或上游项目，而不必复制 API、去重和核验逻辑。

运行离线校验：

    python -m unittest discover -s research-toolkit/tests -v
    python evals/research-stack/score_eval.py lint

完整设计与扩展门槛见 [docs/research-stack-architecture.md](docs/research-stack-architecture.md)。

## 安装

### PowerShell 一键安装

在仓库根目录运行：

```powershell
.\scripts\install.ps1
```

默认安装到 `$env:USERPROFILE\.codex\skills`。安装后重新打开 Codex，或开始一个新任务，让技能列表重新加载。

只安装指定技能：

```powershell
.\scripts\install.ps1 -Skills evidence-research,stock-analysis
```

预览操作而不复制文件：

```powershell
.\scripts\install.ps1 -WhatIf
```

### 手动安装

把所需技能的完整目录复制到：

```text
C:\Users\<你的用户名>\.codex\skills\<skill-name>
```

不要修改技能目录名或 `SKILL.md` 中的 `name`，否则 `$skill-name` 显式调用可能失效。

## 使用方式

可以显式指定技能：

```text
使用 $stock-analysis 分析这家公司近五年的利润质量和现金流风险。
```

也可以直接用自然语言描述任务；Codex 会依据 `description` 自动选择匹配技能。对重要任务建议显式写出 `$skill-name`，便于确认实际使用的工作流。

这些是本地 Codex Skills，普通 ChatGPT 网页对话不会自动读取本机的 `.codex\skills` 目录。

## 维护约定

- 活动入口是每个目录下的 `SKILL.md`。
- `references/SKILL.en.md` 保存英文入口备份，便于回滚及对照上游升级。
- 上游专业 references 和脚本尽量保持原貌，中文调整优先集中在入口和用户界面元数据。
- 新增或更新技能后，应运行官方 `quick_validate.py`，并对有关脚本做最小冒烟测试。
- 跨平台迁移只复制经过选择的能力，不复制对方平台的 frontmatter、工具假设或持久化行为。
- 上下文预算使用稳定字符数复测，不把中文字符数伪装成精确 Token：`python scripts/audit_context.py`。
- 禁止提交 API Key、Token、Cookie、私钥、账号数据、公司机密或真实用户记忆。

## 来源与许可证

本仓库包含基于开源项目改编的内容，详细来源见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。仓库内容按 MIT License 发布；上游内容仍保留其原始版权和许可条件。
