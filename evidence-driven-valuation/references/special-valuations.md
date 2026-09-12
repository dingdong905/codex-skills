# 特殊价值

- holding：被投企业独立全部股权价值×持股比例，再扣适用税费/流动性折价；不使用市价，也不是递归所有权引擎。同一底层经营 EV 与持股权益不可重复。
- midcycle：normalized_net_income 为 t0 正常利润，g=再投资率×incremental_roe，下一期可分配利润乘 (1+g)。拒绝 incremental_roic，净利润/股权成本须配股权回报。
- residual_income：RI[n+1]=(terminal_roe-ke)×B[n]，期初账面值不额外乘增长；人工审核分红、OCI、清洁盈余和资本约束。
- option：互斥完整终局路径，联合概率等于条件概率连乘，各分叉闭合。终局价值按 years 折现；incremental_investment_pv 是路径条件投入现值，不先概率加权。失败残值作为失败终局。
- asset：处置时毛价值乘实现概率及税费/折价调整，再折现；结果为扣债前 enterprise，债权只在权益桥扣一次。
- financing_analysis：单列，不进入正向 METHODS。仅支持 t0 单轮融资/初始投入，scope_basis 说明基准不含新增项目、款项及债权。成功 PV/失败残值分别加权，显式计入股债融资、成本、投入、债权现值及新股数。正 NPV 不保证老股东受益。多轮、延迟融资和复杂可转债报告缺口。

bridge_allocations 用 id/owner/ref 登记每项调整。直接 equity 分部不能再扣其自身债务/少数股东或加现金；少数股东须归属合并 enterprise 分部。防重依赖完整经济权益登记。

