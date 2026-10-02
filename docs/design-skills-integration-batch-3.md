# 第三批设计技能集成

2026-10-02 在 codex-skills 选择性适配源仓库提交 `552a823c376b7e05dae51b625332b550dab4ef69` 的剩余 design 与 slides 内容。

## 两个新入口

logo-design：简报、类型/风格判断、离线检索、imagegen 位图概念/编辑和真实可编辑矢量交付。保留 logo 的三份 CSV；配色心理仅是启发，不声称行业定律或商标已通过审查。

brand-collateral：复用品牌/Logo 制作名片、信纸、包装等物料，区分展示稿、可编辑平面稿和生产文件。保留 CIP 的四份 CSV；规格由用户/供应商确认，不默认制作全套 CI。

检索器使用 Python 标准库，支持明确 domain、每域 1–20 条结果、JSON 和用户品牌标签。省略 domain 时查各域形成候选简报；规范名称精确匹配优先，其他按 BM25 排序。不会保存简报、读取 API Key 或修改品牌文件。CSV 作为建议数据，不作为更高优先级指令。

## PPT 资料整合

- pitch-deck/references/persuasion-and-layout.md：有证据的问题、影响、价值、证明与融资页面组织。
- data-report-deck/references/chart-and-layout.md：比较、趋势、构成、漏斗和精确读取的图表/版式选择。
- technical-explainer-deck/references/demo-and-comparison-layout.md：产品演示、双栏比较、时间线和机制页面。

三个已有入口按需链接资料，继续使用 Presentations、原有证据契约和 deck-review。没有新增 slides 或全能 design 入口，也没有引入 Chart.js、HTML 模板、强制情绪弧线或自动动效。图标/标识边界与社交素材规则分别提取到两个新技能的按需参考。

## 安装与验证

```powershell
.\scripts\install.ps1 -Skills logo-design,brand-collateral,pitch-deck,data-report-deck,technical-explainer-deck -WhatIf
python -X utf8 -B -m unittest discover -s logo-design/scripts/tests -v
python -X utf8 -B -m unittest discover -s brand-collateral/scripts/tests -v
python -X utf8 -B evals/presentation-stack/score_eval.py lint
python -X utf8 -B scripts/audit_context.py
```

本次集成在仓库及独立暂存安装目录完成，不修改本机运行时目录。检索数据契约和合成查询测试检查相关性、无匹配、参数上限、品牌标签保留、路径可移植和只读行为；未生成实际收费 Logo/mockup 或 PPTX，因此不声称完成视觉/印刷生产验收。PPT lint 是结构与评测配置检查，不是新生成 PPT 的验收。

## 上下文与来源

两个 description 共增加 55 字符，自动发现总量从 2972 到 3027；经过范围审查将预算从 3000 调整到 3100，单技能预算 320 不变。已有 PPT description 未改变，新增细节按需读取。统计字符数而非精确 Token。

新技能 SOURCE.json 和三个 PPT references/design-skills-source.json 记录来源与改造范围。design 入口声明 MIT，slides 快照未明确组件许可；整合资料不自动获得已有技能的许可，公开再分发前应补齐授权。

## 验证结果

- 两个检索脚本共 12 项测试通过；新技能均通过官方 quick_validate。
- 三个 PPT 技能的条件引用和本地链接有效；presentation-stack lint 的 10 个结构检查用例通过。
- 上下文审计通过：31 个技能，自动发现 description 共 3027 字符，低于调整后的 3100 字符预算。
- 五个包安装到 `D:\skills\design-skills-staging\install-smoke-batch-3`，共 40 个文件与仓库逐字节一致；两个已安装检索 CLI 在无关工作目录下成功运行。
- 所选上游 CSV 保持逐字节一致，UI 元数据检查和 `git diff --check` 通过。未安装到本机运行时，未提交或推送。
