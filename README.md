# Codex Skills 中文增强集

面向中文用户维护的个人 Codex Skills 仓库，重点增强：

- 多来源信息检索、证据分级与交叉核验
- 上市公司基本面、财报洞察与财务取证
- 研究材料摘要、比较与信息整合
- Codex 上下文治理与 Token 节省
- 长期记忆整理、冲突处理与过期管理

技能调用名保持英文，正文和界面说明采用中文；必要的英文关键词会保留，以兼容中英文自动触发。

## 技能目录

| 技能 | 用途 | 示例调用 |
| --- | --- | --- |
| `academic-search` | 跨学科论文检索、证据核验与生活启示 | `使用 $academic-search 找睡眠改善的可靠研究` |
| `evidence-research` | 当前、多来源、可审计的信息研究 | `使用 $evidence-research 调查……` |
| `stock-analysis` | 上市公司基本面、估值和财务取证 | `使用 $stock-analysis 分析腾讯最新财报` |
| `financial-analyst` | 财务比率、DCF、预算差异与预测 | `使用 $financial-analyst 建立 DCF` |
| `research-summarizer` | 已提供论文、报告和网页的结构化摘要 | `使用 $research-summarizer 比较这些报告` |
| `context-budget` | 审计上下文膨胀并减少 Token 消耗 | `使用 $context-budget 审计当前配置` |
| `memory-curator` | 管理 Codex 记忆、项目约定和任务交接 | `使用 $memory-curator 整理长期记忆` |

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
- 禁止提交 API Key、Token、Cookie、私钥、账号数据、公司机密或真实用户记忆。

## 来源与许可证

本仓库包含基于开源项目改编的内容，详细来源见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。仓库内容按 MIT License 发布；上游内容仍保留其原始版权和许可条件。
