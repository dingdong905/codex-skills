# 13. Worked example C — renormalisation when data is missing

来源：stock-analysis/references/11-scoring-rubric.md；原许可保留。仅作演示，不能作为默认参数。

## 13. Worked example C — renormalisation when data is missing

A recently listed company: no governance history worth scoring and no reliable multi-year growth series. Six of eight categories carry data.

| Category | Default weight | Score | Renormalised weight | Contribution |
|---|---|---|---|---|
| Business quality | 15% | 6.0 | 19.2% | 1.15 |
| Profitability | 20% | 8.0 | 25.6% | 2.05 |
| Earnings quality | 15% | 7.0 | 19.2% | 1.34 |
| Balance sheet | 12% | 6.5 | 15.4% | 1.00 |
| Growth | 12% | *no data* | dropped | — |
| Governance | 10% | *no data* | dropped | — |
| Valuation | 10% | 5.0 | 12.8% | 0.64 |
| Risk | 6% | 6.0 | 7.7% | 0.46 |
| **Composite** | | | **100%** | **6.65 — INDICATIVE ONLY** |

Category coverage is 78%, above the 70% floor — but governance carries a default weight of 10%, so the empty-major-category rule fires and the composite is marked indicative. That is the correct outcome: a company whose governance you have not assessed is not a 6.65, it is an unfinished analysis.

Had the two missing categories been scored 0 instead of dropped, the composite would read **5.19** — a full grade lower, and lower purely because of what the analyst could not find. The report would then be describing the state of the data as though it were the state of the business.

---
