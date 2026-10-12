# 状态检查契约

scripts/handoff_state.py 使用 Python 3.9+ 标准库；Git 工作区还需要 git。它不导出对话、不读取凭据、不运行测试、不联网，也不把快照当作恢复备份。

## snapshot

传入明确目录与需要核验的相关文件，生成 JSON；文件路径相对工作目录。应包含会影响下一步的已修改文件和相关未跟踪产物，避免把凭据文件列入选择。

    python -B <skill-dir>/scripts/handoff_state.py snapshot --workspace <workspace> --file <relative-file> --output <snapshot.json>

--file 可重复。--output 使用独占创建，已有文件直接失败；省略时输出到 stdout。快照记录目录、UTC 观察时间、Git root/HEAD/分支/status、已暂存和未暂存 diff 的 SHA-256、所选文件的 SHA-256。不存文件内容或 diff 原文。Git status 覆盖整个仓库，文件哈希仅覆盖明确选择的文件；未跟踪文件内容变化只有被选择时才能被发现。

所选文件须解析到工作目录内；越界、目录、缺失文件失败，不静默跳过。子目录作为工作区时记录真实 Git root。没有 Git 仓库时记录 git=null；若 Git 不可用则在 limitations 中披露，check 必须在 Git 能力变化时报告差异。

采集期间不要并行写相关文件；采集不是事务快照，快照时间也不是测试时间。Git diff 哈希受 Git 配置/版本影响，应结合路径和文件哈希解释差异。先审阅 stdout 或新文件，确认没有不该传递的路径名称。

## check

    python -B <skill-dir>/scripts/handoff_state.py check --snapshot <snapshot.json> --workspace <current-workspace>

比较当前目录、Git 状态和所选文件哈希，发现任何差异返回非零并报告差异字段。状态比较忽略观察时间，缺失/越界文件视为核验失败。Git 状态匹配不证明测试通过；SHA-256 只证明字节一致，不证明文档正确。

--allow-relocation 用于已确认的跨目录映射，仅允许工作目录和 Git root 前缀改变；HEAD、分支、status、diff 和文件哈希仍须比较。此参数不会授权访问另一工作区，Skill 必须先确认当前可访问位置及映射依据。

snapshot --output 应放在 workspace 外，或已被用户项目忽略的目录，否则生成的未跟踪快照会改变 Git status。接手时交接文档本身造成的已知差异可解释为新增笔记，不据此省略其他差异。

## validate

    python -B <skill-dir>/scripts/handoff_state.py validate <handoff.md>

检查模板核心章节有内容、“下一步”非空、未填模板提示和常见凭据模式。错误信息只给模式或章节名，不打印命中的密钥。退出码：0 表示结构/常见模式检查通过，1 表示差异或校验失败，2 表示输入/执行错误。

此检查是辅助质量门。自然语言隐私、业务秘密、授权合理性及证据真实性仍需语义审阅；不能把“未匹配常见模式”称作安全保证。
