# 可执行充分性闸门

先定义完整 research_plan，不从已有证据反推业务清单。

计划包含 defined_at、materiality_threshold、materiality_basis、businesses、rules。业务包含 name、weight、weight_basis、industry、method、routing_basis、economic_ids、drivers，可用 material_override=true 强制重大。权重总和 1，经济权益 ID 不重叠。

rules 按 business/driver 索引，明确 min_independent、min_primary（整数）、max_age_hours、min_coverage、rationale。一个原始来源只是程序下限，不是通用充分标准；按风险论证阈值，不调低直到通过。

evidence_gate 包含同一 as_of、status=pass、critical_missing=[]、material_conflicts=[]、drivers。每 driver 包含 business_line、name、scope、record_ids、bounds_refs=[下界引用,上界引用]、causal_ref。

脚本重算重大驱动覆盖、source_group 独立组数、primary_confirmation 组数、每条覆盖下限、观察时效、口径、区间与因果引用支持集、隐藏的同业务驱动 missing/conflicted。情景值必须在区间内。

输入 pass 不是结论；输出 evidence_audit.computed_status 为 pass/conditional，违规非零退出。人工仍需核验原文、实际独立性、区间合理性、覆盖分母及未登记业务。不能以手填 sufficient 或计数替代证据。

