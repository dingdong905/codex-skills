# 第一批设计技能集成

2026-10-02 从 [dingdong905/design-skills](https://github.com/dingdong905/design-skills) 的提交 `552a823c376b7e05dae51b625332b550dab4ef69` 选择性适配。集合来自 Stramony/design-skills；每个技能的 SOURCE.json 记录来源、范围和许可状态。

## 分工与触发

- `ui-ux-pro-max`：设计建议检索。保留本地数据和标准库脚本；入口精简，规则按需查阅。实际包含 21 个技术栈；上游明确排除了 SwiftUI 数据，已取消其 CLI 支持并修正计数。版本建议仍需对照项目版本与官方文档。
- `brand`：品牌事实、语气、指南、资产规范。Node.js 工具不依赖 Gemini；同步不会重命名品牌、删除既有色阶、推导新色阶或覆盖状态色。指南解析需使用文档中约定的英文颜色标签。
- `design-system`：Token 架构、组件状态、JSON→CSS 与硬编码候选扫描。未导入上游演示数据、Chart.js、背景下载和幻灯片工具。

网站构建/发布、Figma 写入和 PPTX 制作继续使用各自已有技能。设计检索输出为输入建议，不替换现有执行层或品牌事实。技能默认可自动选择，description 用任务边界减少重叠。

## 安装

在仓库根目录运行：

```powershell
.\scripts\install.ps1 -Skills ui-ux-pro-max,brand,design-system -WhatIf
.\scripts\install.ps1 -Skills ui-ux-pro-max,brand,design-system
```

品牌同步需要同一安装根下的 `design-system`；单独复制 brand 时需显式指定 `--generator`。安装后在新的技能加载周期中使用。仓库是源，本次集成不自动发布远程仓库。

## 验证

```powershell
python -B ui-ux-pro-max/scripts/validate_data.py
python -B -m unittest discover -s ui-ux-pro-max/scripts/tests
node --test brand/scripts/tests/*.test.cjs design-system/scripts/tests/*.test.cjs
```

上游两个测试文件依赖未随快照提供的 catalog-refresh/relevance-evaluator 工具；未导入这两个测试，不冒充完整上游测试套件。其余检索、数据和主题生成回归保留；Native/Desktop 测试取消未提供的 SwiftUI 用例。

## 来源与许可

集合 README 明确不提供统一许可。design-system 入口声明 MIT；brand 与 ui-ux-pro-max 快照缺少组件级明确许可声明，不将它们擅自标记为本仓库 MIT。字体、图标数据保留原有 provenance、字体许可证与快照信息。公开再分发前需要补齐组件授权与所需许可文本；SOURCE.json 随安装保留。

## 本次验证结果

12 个 domain、21 个 stack 及 reasoning 数据校验通过；130 项已保留的 UI 回归与 21 项品牌/Token 行为测试全部通过。三个技能通过官方 quick_validate.py（Windows 使用 `python -X utf8`）。安装清单经过 WhatIf 与独立暂存安装验证。新增入口约 3 KB/技能，参考规则按需读取；这些是文件体积，不能当作精确 Token 数。

## 上下文预算复核

本批前自动发现的 description 合计 2609 字符，已超过原预算 2400；新增三个 description 合计 242 字符，集成后为 2851。审查触发边界后将预算调整为 3000，保留 149 字符余量；单技能预算 320 不变。未修改其他技能的 description 或调用策略。

路由核对：后台接口/数据库不使用设计技能；品牌语气/指南使用 brand；JSON Token/暗色主题别名使用 design-system；页面配色或键盘交互检索使用 ui-ux-pro-max；PPT 制作继续走原有演示技能，网站部署与 Figma 修改继续走已有执行工具。组合需求可按顺序使用相关技能，避免加载全部资料。
