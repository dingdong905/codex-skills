# find-skills 集成说明

2026-10-02 在 Codex 源仓库接入精简版。来源为 Vercel Labs skills/find-skills，固定提交 3694740352eeef5cdd689af694c485f1ff62eec3；MIT 许可和版权随包保留。

入口限定为找技能、比较候选与扩展技能库。先复用现有能力；搜索可使用现有 GitHub/浏览器工具，CLI 仅为可选后备。CLI 版本需核验并固定，默认关闭遥测；搜索失败不能等同零结果。候选比较增加源码、许可、维护、平台兼容、能力重叠与上下文开销。

用户授权接入时在平台仓库适配，记录 SOURCE.json，运行预算及结构检查、隔离安装验证。未将第三方命令行程序或其依赖打包。正常任务执行不会触发技能搜索；接入仓库不自动安装到运行时或发布。

## 验证结果

- 官方 quick_validate、UI 元数据、条件引用、来源记录及 MIT 许可文本检查通过。
- 上下文审计通过：description 新增 39 字符，自动发现总量 3027 → 3066，保留 3100 字符上限；入口正文连同 frontmatter 共 874 字符。这里统计字符，不估算精确 Token。
- 安装脚本 -WhatIf 通过；隔离安装到 D:\skills\design-skills-staging\install-smoke-find-skills，共 6 个文件与源仓库逐字节一致。
- git diff --check 通过。未新增执行脚本，未运行外部 Skills CLI；本次结构/打包检查不代表真实候选推荐质量的行为验收。
- 未安装到本机运行时，未提交、推送或发布；已有其他批次及 Android 变更保留。
