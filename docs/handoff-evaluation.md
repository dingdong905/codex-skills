# Handoff 开源选型与 Codex Skill 适配

核验日期：2026-10-10（Asia/Shanghai）。用户只记得名称 handoff，无法据此唯一识别仓库；下列两个同名仓库都符合部分描述。当前选择基于已观察到的 Windows/PowerShell、Codex、源码仓库优先、通用规则与案例分层，以及现有 memory-curator/context-budget；没有把 WorkBuddy 导出能力或自动 hooks 视为已有条件。

## 结论

默认采用一个独立重写的本地 handoff Skill：目标导向交接 + 关键产物引用 + 证据状态 + 接手现场核验。它可准备交接，也可在当前用户授权下从交接继续。完整历史、云服务和自动记录工具保留为条件选项，不增加常驻服务或全局 hooks。

用户需要“当前聊天换会话续做”时，纯 Skill 的成本最低；需要逐字历史溯源时，AgentHandoff 更匹配；需要 Claude Code/Cursor 每个工具动作自动记录时，再考虑 rosehgal/handoff；需要可分享网页时，再考虑 open-grove/handoff。

## 候选比较

“贴合度”是基于本地环境和代码阅读的工程判断，不是实际性能评分。“好用”仅指流程复杂度、可读性和当前适用性；没有运行上游项目验证其稳定性。

| 仓库 | 已核验能力与限制 | 当前贴合度 / 选择 |
| --- | --- | --- |
| [open-grove/handoff](https://github.com/open-grove/handoff) | Go CLI；Codex/Claude Code/Pi/OpenCode；当前会话准备 Markdown；默认 create 发布到服务；本机 session locate 单独支持本地路径；提供 Windows 发行包说明 | 中；适合明确跨人分享。默认本地交接无需引入服务 |
| [rosehgal/handoff](https://github.com/rosehgal/handoff) | Go 二进制 + Claude/Cursor hooks；JSONL 事件日志与 Markdown 投影；Windows 发行包说明；安装 client 选项是 all/claude/cursor，未见 Codex 集成 | 当前偏低；若之后主用 Claude/Cursor 可选。工具日志不能代替用户目标与成功证据 |
| [klittle32/handoff-skill](https://github.com/klittle32/handoff-skill) | 纯 Skill；目标驱动、文件引用、首句；可选 Python 验证；默认偏临时交接文件 | 高；借鉴交接结构，改为项目内任务笔记优先、中文、Codex 授权边界 |
| [timyeou1234/context-handoff](https://github.com/timyeou1234/context-handoff) | Codex Skill + hook 插件；安全检查点、接手核验、目录兼容性；包含置顶/归档和遥测阈值 | 核验机制高，完整插件中；保留核验思想，不默认引入 hooks、阈值、置顶或归档 |
| [jugugug/AgentHandoff](https://github.com/jugugug/AgentHandoff) | Python 标准库、Codex App Server thread/read；摘要/索引/原文本分层，字节完整性核验；需精确线程 ID；不自动脱敏 | 精确溯源高、日常交接中；借鉴渐进读取，不复制 App Server exporter，也不把任务实例安装为常驻 Skill |
| [platonissex/session-handoff](https://github.com/platonissex/session-handoff) | Python 标准库；本地 UI/CLI；Qoder/Claude/Codex/Grok 来源；seed/dialog/index 和首句；清理工具噪声 | 多 CLI 切换中高；适配器格式需按本机版本实测，关键工具验证证据另行保留 |
| [jumpifequal/handoff-skill](https://github.com/jumpifequal/handoff-skill) | 通用 Skill；明确来源、精确 WIP、一个下一步；可选 Node hooks；README 许可表述与 LICENSE 不一致 | 手工交接高；优先引用已存产物，避免全文复制；不安装 hooks |

## 证据与反证

- 来源包括每个仓库 README、GitHub 仓库元数据、main 提交及 LICENSE；深入核验 klittle32 与 timyeou 的 SKILL.md、AgentHandoff exporter、open-grove 的 CLI Skill 和 internal/client/client.go、rosehgal 的命令入口。
- open-grove 的 HTTP client 在创建时 POST /v1/handoffs；README 也说明发布准备内容和附件范围，确认 create 并非默认纯本地写文件。
- AgentHandoff exporter 启动 codex app-server，并以 CODEX_THREAD_ID 指定 thread/read；缺少 ID 明确失败。README 说明导出不自动脱敏，不能称为无配置通用导出。
- rosehgal README 与命令源码均以 Claude/Cursor 为集成对象；这只是“未见 Codex 适配”，不推断它在其他宿主永远不可用。
- jumpifequal README 末尾仍称没有许可，但检视的 LICENSE 为 MIT，版权为 2026 Jumpifequal，API 也标 MIT；以实际许可文件为准，保留文档差异。
- 快照时七个候选各只有 0–2 个 star，都是规模较小的项目；不能用热度证明成熟，也不能用低热度证明质量差。
- 仓库 pushed_at 可以因其他分支变化而晚于 main 提交时间；不把 pushed_at 冒充本次检查版本的发布日期。固定提交记录随 Skill 的 SOURCE.json 安装携带。

资料主要来自作者仓库，README 与源代码可交叉核验机制，但不是独立生产使用证明。未实测上游工具、Windows 二进制、hooks、完整聊天迁移或云部署，不承诺无损会话迁移。

## 实现与治理

新增 handoff/SKILL.md、空白模板、状态 snapshot/check/validate 标准库脚本、测试、合成场景及 index.json、元数据和来源记录。脚本只采集明确目录和文件哈希，Git diff 仅保存哈希；不会提取原始聊天、联网或恢复代码。

memory-curator 继续负责长期偏好与上下文层级；context-budget 继续负责开销审计；handoff 负责短期任务续做。一个统一 Skill 避免把 prepare/resume 拆成多个同义入口。没有修改这两个已有 Skill 的调用策略。

源码先进入 Codex 来源仓库；安装只复制新增 handoff 到本机 Codex 技能目录，不替换已有技能。WorkBuddy 不是本次实现目标；Markdown 交接内容可供其他工具读取，但不声称原生导出或平台工具适配已经完成。

验证：10 项隔离脚本测试通过；全仓库治理检查 34 个 Skill、0 错误。官方 quick_validate 在 Python UTF-8 模式下通过；现有源码工作区 snapshot/check 实测匹配；安装清单 WhatIf 及实际安装成功，本机安装的 11 个文件与源目录逐字节哈希一致。结构校验不能证明未来每次接手都正确；状态哈希不验证测试结果或语义。
