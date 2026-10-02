# 搜索方式与故障边界

优先使用当前已配置的 GitHub 连接器或浏览器；可访问 skills.sh 的搜索页/API 时，用普通任务关键词搜索，再到来源仓库核验。关键词会传给外部服务，不把密钥、内部文档正文或私有路径写入搜索词。

CLI 是可选后备，Skill 自身不要求 Node 或 npm。使用前核验可用版本并固定版本，不运行裸 npx skills 的浮动最新版；本次上游快照 package.json 为 1.7.0，要求 Node >=22.20.0，这不是对 npm 发布状态的验证。

PowerShell 示例（<已核验版本> 应替换为实际版本）：

    $env:DISABLE_TELEMETRY = '1'
    npx --yes skills@<已核验版本> find 'react performance' --owner vercel-labs

仅在当前进程设置遥测开关；如已有值，结束后恢复原值。关闭遥测仍会向 skills.sh 发出搜索请求。非交互查询只搜索；无查询的交互模式选中结果可能进入安装流程，因此使用带查询的命令。不使用 add/update 来测试搜索。

上游搜索函数将 HTTP 错误与异常转成空列表，CLI 的“No skills found”无法单独证明零结果。出现空结果时，用独立只读请求检查服务状态或用 GitHub 搜索交叉核验；无法核验则报告“未找到候选，搜索服务状态未确认”。避免无限重试或启动额外安装器。
