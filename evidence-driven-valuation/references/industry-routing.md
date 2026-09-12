# 已实现行业路由

按经济实质分类，不能为通过白名单伪装行业。

| industry | method | basis |
|---|---|---|
| nonfinancial | dcf | enterprise |
| bank | residual_income | equity |
| cyclical | midcycle / dcf | equity / enterprise |
| holding | holding | equity |
| new_product | option | 显式 enterprise/equity |
| asset_disposal | asset | enterprise，扣债之前 |

集团分部路由再做 SOTP。保险、矿业、REIT、生物科技等专门模块未实现，报告方法缺口，不套通用倍数/DCF。证券资管等也不能未实现就加入白名单。

银行仅有剩余收益公式，不自动验证资本充足、OCI/清洁盈余。周期需外部论证正常利润及股权回报。最低驱动集合见脚本 DRIVERS，标签不能证明经济适用性。

