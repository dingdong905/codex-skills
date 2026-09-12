# 数据提供者契约

借鉴 OpenBB 统一接口思路；目前未实现实时供应商适配器。

provider 元数据包括 provider_id、provider_name、dataset、source_type、query、coverage、frequency、latency、timezone、revision_policy、license_or_terms、retrieved_at、point_in_time_capable。

响应包示意：

```json
{"provider":{},"as_of":"2026-01-02T12:00:00Z","records":[],"warnings":[],"next_cursor":null}
```

这是提供者响应而非完整估值输入。records 按 [evidence-ledger.md](evidence-ledger.md) 标准化，保留原始响应、查询和分页。公开、修订、可得、采集时间分别记录。无法证明历史可用性时 point_in_time_capable=false，不用于历史研究。失败、权限不足和陈旧缓存必须告警，不静默插值或回退旧期。切换来源不能改变指标口径。

