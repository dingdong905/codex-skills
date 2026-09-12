# 事实账本 v2

顶层 as_of 为带时区 ISO 时间戳，例如 2026-01-02T12:00:00Z；records 为非空列表。

每条记录必需字段：

```text
record_id entity business_line supply_chain_stage metric driver value unit
geography product_or_project counterparty scope coverage
observed_at published_at vintage_at available_at collected_at
vintage_id snapshot_reference
source_title source_publisher source_group source_url_or_file source_excerpt source_kind
evidence_class confidence cross_checks status notes
```

- 所有时间含时区，按 UTC 比较。observed_at 是发生时间，confirmed 不能晚于截止；未确认状态可为 null，不能编造日期。
- published_at 首次发布，vintage_at 所用版本发布，available_at 该版本实际可得，collected_at 本次采集。published ≤ vintage ≤ available ≤ collected，available ≤ as_of。
- 可在截止后采集真实历史快照，不可使用截止后修订。snapshot_reference 和 vintage_id 必须可核验；脚本不下载快照或验证内容。
- business_line/driver 明确业务与变量；scope 描述产品、地区、期间；coverage 是该口径覆盖比例 [0,1]，notes 解释分母和依据。
- source_group 按原始来源归组，同源转载共组。source_kind 为 fundamental/market，市场信息不能支持正向价值。
- evidence_class：physical_flow、price_order_inventory、primary_confirmation、secondary_lead、unverified_lead。
- confidence：high/medium/low；notes 写依据。
- status：confirmed/source_claim/unverified/conflicted/missing。calculated 停用，派生数值放估值节点。
- cross_checks 为存在的其他 record_id，不允许自引用；引用存在不代表语义交叉核验通过。
- 只有 missing 可用 null 值；禁止布尔和非有限数字。文字观察不能直接绑定定量估值。
- 框架订单、渠道发货、规划产能分别标记 framework_order/channel_shipment/planned_capacity；不能改标签绕过转换。

运行 `python -B scripts/validate_ledger.py <ledger.json>`。保留冲突和反证，原始值不能被标准化值覆盖。

