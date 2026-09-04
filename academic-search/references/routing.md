# 学科路由表

| 请求特征 | 路由 | 说明 |
| --- | --- | --- |
| LLM、机器学习、计算机系统、软件工程、数据集、基准、代码复现 | ai-computing-research | 处理前沿、版本、代码/权重、算力和 benchmark 风险 |
| 疾病、药物、治疗、诊断、预防、营养、睡眠、运动、心理干预、临床试验 | biomedical-evidence | 采用医学证据层级和独立安全边界 |
| 用户给定论文/报告，只要求摘要或比较 | research-summarizer | 不做新的网上发现 |
| 政策、市场、新闻、公司等非论文来源也决定结论 | evidence-research + 相应专业 Skill | 分开维护学术证据与现实资料 |
| 历史、地理、天文、社会学、哲学等尚无专业 Skill | 通用回退 | 读取 fallback.md，明确标注回退 |
| 同时涉及 AI 医疗、计算社会科学等多个领域 | 分别路由后合并 | 各领域独立评价，最后综合 |

## 边界案例

- “AI 能否诊断癌症”：AI 性能和复现走 ai-computing-research；临床有效性、偏倚和安全走 biomedical-evidence。
- “社交媒体对青少年抑郁的影响”：心理健康与因果证据走 biomedical-evidence；平台治理或社会理论可走通用回退/evidence-research。
- “历史地图自动识别”：算法部分走 ai-computing-research；史料解释部分走通用回退。
