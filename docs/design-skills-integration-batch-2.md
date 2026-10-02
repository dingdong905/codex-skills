# 第二批设计技能集成

2026-10-02 在 `D:\skills\codex-skills` 集成 `hallmark`、`banner-design`、`ui-styling`。采用与第一批相同的 [源仓库](https://github.com/dingdong905/design-skills) 提交 `552a823c376b7e05dae51b625332b550dab4ef69`，保持更新可追踪。

## 范围与分工

- hallmark 只负责页面视觉审查、结构重设计和参考分析。局部组件不套全页流程；保留品牌/路由/业务职责，基于真实渲染证据判断。按模式加载四份精简资料。
- banner-design 负责横幅、封面和社交素材。内置 imagegen 负责位图素材/编辑，可编辑排版负责准确文案与多尺寸版本；PNG 检查器核对物理尺寸、字节数和容器基本结构，视觉与解码另由实际查看确认。
- ui-styling 限定到现有 React/shadcn/Tailwind 项目，区分 v3/v4 配置与主题映射。先读本地组件 API 和锁定版本，沿用组件库，不用初始化或全量组件安装覆盖已有实现。

UI/UX 选型走 ui-ux-pro-max，品牌事实走 brand，Token 架构走 design-system，现有网站/Figma/PPT 执行层保持各自职责。新三个技能默认可自动选择，只在对应任务需要时加载；普通组件实现不会强制进入 Hallmark 审查流程。

## 安装与依赖

```powershell
.\scripts\install.ps1 -Skills hallmark,banner-design,ui-styling -WhatIf
.\scripts\install.ps1 -Skills hallmark,banner-design,ui-styling
```

本次仅修改仓库并验证独立暂存安装，不改本机运行时技能目录。横幅检查只依赖 Python 标准库；素材生成和浏览器导出使用任务环境已有能力，技能安装不会安装 Gemini、Node 包或浏览器。没有真实图片生成和项目实现任务时不调用收费生图或编造实际页面验收。

## 验证及限制

```powershell
python -X utf8 -B -m unittest discover -s banner-design/scripts/tests -v
python -X utf8 -B scripts/audit_context.py
```

横幅脚本 12 项合成图片回归已通过；检查正常尺寸、错尺寸、字节上限、CRC 错误、截断、假 PNG、缺 IDAT、索引色缺 palette、透明能力、零尺寸、尾随数据与 CLI 退出码。该脚本不编辑图片、不解码像素，也不证明图片可用作印刷文件。

三个入口通过官方 quick_validate.py；资料链接、UI metadata 和旧平台工具依赖另做静态检查。素材生成和真实 React 项目行为未在本次接入中执行，因此没有声称它们已通过生产视觉验收。

## 发现上下文与来源

第二批前自动 description 为 2851 字符，三个精简入口增加 121 字符，集成后 2972，保持总预算 3000，单技能预算 320 不变。字符数不是模型 Token 数。

hallmark 的快照缺少明确许可；banner-design 入口声明 MIT；ui-styling 存在 MIT 声明与附带 Apache-2.0 文件冲突，文件完整保留并记录。公开再分发前仍需明确相应授权，详见各技能 SOURCE.json 与 THIRD_PARTY_NOTICES.md。

独立暂存安装验证：三个技能共 22 个文件与源目录逐字节一致；安装后的横幅 CLI 可运行，安装清单 WhatIf 通过。新增入口 2.5–2.8 KB，第二批未引入额外第三方运行时包。
