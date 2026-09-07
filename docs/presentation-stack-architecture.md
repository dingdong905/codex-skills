# PPT Skills 混合架构

## 设计结论

专业分类按“观众看完后要做什么”划分，而不是按行业或视觉风格划分。这样同一个 AI Infra 主题可以根据目的进入技术讲解或管理决策，避免一套万能 Skill 同时加载所有规则。

```text
presentation-studio（薄编排器）
├─ technical-explainer-deck（精细样板）
├─ executive-decision-deck（基础版）
├─ research-presentation（基础版）
├─ pitch-deck（基础版）
├─ data-report-deck（基础版）
└─ teaching-deck（基础版）

Presentations（统一执行层）
├─ PPTX 读取、编辑与模板跟随
├─ 可编辑表格、图表和必要图形
├─ @oai/artifact-tool 构建
└─ 渲染和基础验证

deck-review + evals/presentation-stack（独立 QA 与评测）
```

需求理解、叙事、压缩和视觉表达是每个品类内部的能力层，不拆成会自动触发的微型 Skill。否则一次任务会加载多个高度重叠的说明，增加冲突和 Token 开销。

## 样例归纳

两份用户样例共同属于“企业内部技术体系讲解、技术选型与培训型演示”。它们覆盖了挑战地图、概念单位、系统拓扑、参数到场景映射、产品对比、技术演进、生态兼容、故障研究和选型总结。

值得保留的优点：信息完整、技术对象丰富、参数与场景有连接、品牌视觉稳定。需要在新 Skill 中纠正的模式：

- 现场可读字号偏小，部分页面低至约 5–10pt
- 单页文本和对象过多，阅读路径碎片化
- 宽表格承担过多参数，正文与附录没有分层
- 精确规格、价格、供应和兼容性缺少统一来源与截至日期
- 架构全景、局部机制和结论常挤在同一页
- 标题标点、章节编号和分页表达不完全一致

参考文件只用于归纳抽象规则，不提交原始 PPTX、Logo、内部数据或逐页截图。

## 开源复用决策

| 项目 | 许可 | 决策 | 理由 |
| --- | --- | --- | --- |
| `Akxan/ppt-agent-skill` | MIT | 选择性借鉴 | 认知负荷、叙事、视觉层级、数据表达和 failure modes 完整，但整体工作流庞大且会与统一执行层重叠 |
| `CacinieP/ppt-skills` | MIT | 选择性借鉴 | 对中文字体、CJK 溢出、WCAG 对比度、可编辑性和版式契约有实用 QA 思路 |
| `algerchen2024/image-to-editable-pptx` | MIT | 留作独立品类 | 适合截图/扫描页还原，不应混入普通新建演示流程 |
| `presenton/presenton` | Apache-2.0 | 只参考产品工作流 | 完整应用体量过大，不适合作为轻量本地 Skill 依赖 |
| `gitbrent/PptxGenJS` | MIT | 不新增依赖 | 底层能力成熟，但当前 `Presentations` 已提供统一构建层 |
| `anthropics/skills` 的 pptx Skill | 专有许可 | 不复用 | 许可禁止复制、保留副本和创建衍生作品，不适合公开仓库 |

本仓库没有复制 Anthropic 的内容。当前新增脚本为基于 OOXML 公共格式独立实现的静态审计器。

## 能力层映射

| 能力层 | 所在位置 |
| --- | --- |
| 需求理解与路由 | `presentation-studio` 的 `deck-brief` |
| 内容研究 | 复用现有研究和 Data Analytics Skills |
| 叙事、压缩、视觉决策 | 各专业品类 Skill |
| 模板、构建、可编辑对象 | 系统 `Presentations` |
| 数据可视化 | 品类规则 + Data Analytics + `Presentations` |
| 视觉和内容 QA | `deck-review` |
| 演讲备注与问答 | 各品类按需生成 |
| 可测质量和 Token 预算 | `evals/presentation-stack` |

## 下一阶段门槛

先用技术讲解样板完成真实端到端生成和审阅。其他品类只有在至少三个真实用例暴露稳定差异后再增加专用参考资料或脚本。截图还原应作为单独 Skill 引入，避免污染常规 PPT 的可编辑与视觉规则。

