# 统一证据契约（v1）

工具输出是一个 envelope，包含 schema_version、operation、query、fetched_at、records 和 warnings。

每条 record 的稳定字段：

| 字段 | 含义 |
| --- | --- |
| title、authors、year、published、venue | 基本文献信息 |
| identifiers | doi、pmid、pmcid、arxiv、nct 等 |
| abstract | 可为空；不得由标题推测生成 |
| record_type、peer_review_status | 论文/预印本/试验注册等及审核状态 |
| citation_count | 来源返回的当前引用数；不同平台不可直接混比 |
| open_access | is_oa、url、status |
| is_retracted | true、false 或 null；null 表示未查明 |
| urls | 落地页、PDF 或来源记录链接 |
| sources | 提供该记录的平台列表 |
| provenance | 原始来源 ID 与抓取时间 |

专业 Skill 在此基础上添加证据账本：

- claim：论文实际支持的主张。
- evidence_strength：按本领域规则给出的等级及理由。
- limitations：设计、样本、偏倚、版本或外推限制。
- contradictions：支持/反对证据及无法调和之处。
- safety_flags：健康、安全、法律等升级标记。
- practical_implication：现实意义、适用条件和不可推出的行动。
