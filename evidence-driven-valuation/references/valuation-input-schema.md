# 估值输入 v2

可执行完整合成实例见 ../examples/synthetic-handoff.json。它只验证交接，不代表真实充分证据。

## 顶层

必需 schema_version=2、as_of（带时区）、currency、amount_unit、analysis_mode、scope_basis、ledger、nodes、research_plan、evidence_gate、scenarios。可选 reverse_valuation、financing_analysis；未知顶层字段报错。

amount_unit 仅 ones/thousands/millions/billions；金额输入与总价值保持该单位，股数始终是实际 shares。evaluate/CLI 的每股结果转换为 currency/share。比例用 ratio，年数用 years，金额引用用 currency:amount_unit。不能把万股填作 shares 或把万元标作 ones。

analysis_mode 为 independent/conditional。证据无法约束的假设只能 conditional，且输出列明；不是默认值填充许可。scope_basis 解释完整经济边界和未纳入暴露。

ledger 与顶层截止一致，遵循采集 Skill 的 evidence-ledger.md；两 Skill 同级安装。

## 节点和 provenance

nodes 为 ID→节点对象，ID 不与记录冲突。共用 kind、unit、business_line、driver、rationale、available_at、evidence_refs（非空唯一引用列表）。

calculation 另含 op、args（全部为引用，集合等于 evidence_refs）、unit_derivation；支持 identity/add/subtract/multiply/divide/min/max。危险阶段转换还需 conversion_basis。常量也必须来自事实或明确假设。

assumption 另含 value、bounds=[低,高]、bounds_basis、bounded_by_evidence（布尔）。值必须位于有依据的区间内；false 要求 conditional。来源声明不能代替原文审计。

provenance 精确覆盖每个数值叶子，值为一个可解析 ID，例如 explicit_fcff.0、outcomes.0.conditional_probabilities.1。不能用顶层数组引用代替叶子。解析值须与输入相等，业务、driver、单位匹配；拒绝循环、未来版本、未确认记录及正向市场污染。

## 计划和闸门

完整字段及阈值见 evidence-gate.md。DCF 最低驱动 quantity、price、cost、working_capital、capex、cash_flow、discount_rate、terminal_growth，其他方法见脚本 DRIVERS。不能漏业务后手填 pass。

## 情景与权益桥

每情景：name、probability、probability_ref、segments、equity_bridge、bridge_provenance、bridge_allocations。情景概率合计 1，概率引用映射 __group__/probability。每情景覆盖全部登记业务。

segment：name、method、basis、inputs、provenance。路由须与计划一致。

equity_bridge 必须显式包含 cash、debt、lease_liabilities、minority_interest、non_operating_assets、contingent_liabilities、diluted_shares，均非负，股数大于零。bridge_provenance 映射 __group__/对应字段。

bridge_allocations 为除 diluted_shares 外每项的列表；元素 id、owner、ref。空列表仅用于有来源的零余额；合计需与桥一致。owner 为 __parent__ 或 enterprise 分部，少数股东必须归属后者。ID 不能与经济权益或其他调整重复。

股权价值 = enterprise 分部合计 + direct equity 分部合计 + cash + non_operating_assets − debt − lease_liabilities − minority_interest − contingent_liabilities。

## 方法 inputs

- dcf：explicit_fcff（从第1年末开始的年度流）、discount_rate、terminal_growth。
- residual_income：opening_book_value、forecast_net_income、forecast_ending_book_values（等长年度列表）、cost_of_equity、terminal_roe、terminal_growth。
- midcycle：normalized_net_income（t0）、reinvestment_rate、incremental_roe、cost_of_equity。
- holding：intrinsic_equity_value、ownership、tax_leakage、liquidity_discount。
- option：outcomes；每项 name、probability、path（阶段字符串列表）、conditional_probabilities、value_at_resolution、years、discount_rate、incremental_investment_pv。
- asset：assets；每项 name、fair_value、realizability_probability、tax_leakage、haircut、years、discount_rate。

方法输入不能夹带其他字段。经济时点及特殊项限制见 special-valuations.md。

## 独立侧项

reverse_valuation 包含 inputs/provenance，绑定 __reverse__。inputs：current_enterprise_value、base_fcff、discount_rate、terminal_growth、years（正整数）、growth_search_low、growth_search_high。只反推单一恒定增长，不自动识别所有隐含经营变量。

financing_analysis 包含 inputs/provenance/scope_basis，绑定 __financing__。inputs：incremental_fcff、discount_rate、terminal_growth、execution_probability、failure_value、failure_years、equity_proceeds、debt_proceeds、investment_now、issuance_costs、debt_claim_pv、old_shares、new_shares。old_shares 等于基准各情景 diluted_shares。融资仅 t0 单轮，不能与基准重复包含新项目或资金。

正向 evidence_audit 单独保留；存在侧项时 combined_input_audit 列出全部已用假设/未约束条件。侧项不修改独立价值。

## 迁移与运行

旧版输入不可自动兼容：补查时区、版本、真实引用、完整业务和阈值，重建节点与归属；缺失就报告缺口，不为迁移编造证据。

运行 python -B scripts/valuation_engine.py <input.json>。只支持 evaluate/CLI 作为受闸门保护入口；底层公式函数不执行完整审计。

