# 外部方案取舍

本 Skill 的本地流程可独立完成。只有任务需要完整历史、自动捕获或外部分享时才选择其他方案；工具未安装时先检查实际能力，不猜接口。

- **完整原始文本**：jugugug/AgentHandoff 使用 Codex App Server 对指定线程做只读捕获，保留文本与完整性索引。适合逐字溯源；依赖实际 Codex 可执行文件、线程 ID 与接口版本，导出不自动脱敏。不要以“最新会话”替代精确来源，也不要把临时任务导出包安装进长期 Skill 目录。
- **跨 CLI 本地整理**：platonissex/session-handoff 提供本地 UI 和 seed/dialog/index。来源适配器需要按实际日志格式验证；文本清理可能删掉对接手有用的工具证据，应另保存关键验证结果。
- **自动工具日志**：rosehgal/handoff 面向 Claude Code/Cursor hooks。事件日志说明发生过操作，不能证明命令成功或保留全部用户意图；是否接入取决于宿主实际支持的 hook 契约。
- **分享链接**：open-grove/handoff 支持 Codex、Claude Code、Pi、OpenCode。create 默认向服务发布准备好的内容，session locate 是本机路径模式。需要分享时先明确传递内容和目的地；完整上下文附件是额外范围，脱敏只是尽力处理。它不是这里的默认本地存档命令。
- **自动压缩检测**：timyeou1234/context-handoff 还带 Codex hook 插件。可信 hooks、遥测与聊天接口需按当前宿主验证；安装纯 Skill 不等于自动获得检测功能。
- **通用手工交接**：klittle32/handoff-skill 和 jumpifequal/handoff-skill 可作为低依赖方案；前者偏目标和文件引用，后者偏精确工作片段与来源。已在文件中存在的大块内容使用引用，不必每次重复全文。

上述仓库与许可证记录在 SOURCE.json；固定版本的比较、平台适配和未实测部分记录在来源仓库 docs/handoff-evaluation.md。该评估是维护材料，不是每次交接必读内容。
