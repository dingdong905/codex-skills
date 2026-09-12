"""Synthetic, independently inspectable end-to-end inputs; no live company data."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evidence_contract import Audit, ContractError, DRIVERS, driver_for, leaves, unit_for
from valuation_engine import InputError, evaluate, residual_income, midcycle, option_value, asset_value, reflexivity


T = "2026-01-02T12:00:00Z"
EARLY = "2026-01-02T09:00:00Z"


def record(rid, driver, value, unit, business="core"):
    return dict(record_id=rid, entity="Synthetic Issuer", business_line=business,
                supply_chain_stage="accepted_delivery", metric=driver, driver=driver,
                value=value, unit=unit, geography="CN", product_or_project="fixture",
                counterparty="synthetic customer", observed_at=EARLY,
                published_at=EARLY, available_at=EARLY, vintage_at=EARLY,
                vintage_id="v1", snapshot_reference="fixture://" + rid,
                collected_at=T, source_title="Synthetic evidence", source_publisher="Fixture publisher",
                source_group="original-A", source_url_or_file="fixture://" + rid,
                source_excerpt=f"Synthetic {driver} = {value} {unit}",
                evidence_class="primary_confirmation", confidence="high", cross_checks=[],
                status="confirmed", notes="Synthetic test only, no investment use.",
                coverage=1, scope="CN/product", source_kind="fundamental")


def fixture():
    entries = {
        "quantity": (10, "units"), "price": (3, "CNY/unit"),
        "cost": (10, "CNY:ones"), "working_capital": (5, "CNY:ones"),
        "capex": (5, "CNY:ones"), "discount_rate": (.1, "ratio"), "terminal_growth": (0, "ratio"),
    }
    records = [record(k, k, v, u) for k, (v, u) in entries.items()]
    nodes = {}
    def calc(name, op, args, driver):
        nodes[name] = dict(kind="calculation", op=op, args=args, evidence_refs=list(dict.fromkeys(args)),
                           unit="CNY:ones", business_line="core", driver=driver,
                           rationale="Deterministic operating bridge; cost includes cash tax.",
                           available_at=EARLY, unit_derivation="units * CNY/unit = CNY; subtract CNY amounts")
    calc("revenue", "multiply", ["quantity", "price"], "revenue")
    calc("operating_cash", "subtract", ["revenue", "cost"], "operating_cash")
    calc("after_wc", "subtract", ["operating_cash", "working_capital"], "after_wc")
    calc("fcff", "subtract", ["after_wc", "capex"], "cash_flow")
    # Forecast repetition is an explicit assumption, not a historical fact.
    nodes["forecast"] = dict(kind="assumption", value=10, bounds=[10, 10],
                             bounds_basis="Fixture assumes unchanged accepted sales and cash costs for next year",
                             bounded_by_evidence=True, evidence_refs=["fcff"], unit="CNY:ones",
                             business_line="core", driver="cash_flow", rationale="Explicit flat forecast for test", available_at=EARLY)
    bridge = dict(cash=0, debt=0, lease_liabilities=0, minority_interest=0,
                  non_operating_assets=0, contingent_liabilities=0, diluted_shares=10)
    for k, v in bridge.items():
        records.append(record("bridge_" + k, k, v, unit_for(k, "CNY", "ones"), "__group__"))
    records.append(record("scenario_probability", "probability", 1, "ratio", "__group__"))
    drivers = []
    rules = {}
    for d in sorted(DRIVERS["dcf"]):
        ref = "forecast" if d == "cash_flow" else d
        refs = ["quantity", "price", "cost", "working_capital", "capex"] if d == "cash_flow" else [d]
        drivers.append(dict(name=d, business_line="core", record_ids=refs, scope="CN/product", bounds_refs=[ref, ref], causal_ref=ref))
        rules["core/" + d] = dict(min_independent=1, min_primary=1, max_age_hours=24,
                                   min_coverage=.9, rationale="Synthetic full-coverage inputs; real designs require independent judgment")
    return dict(schema_version=2, as_of=T, currency="CNY", amount_unit="ones", analysis_mode="independent",
                scope_basis="One synthetic operation; no subsidiaries, off-balance sheet interests or omitted businesses",
                ledger=dict(as_of=T, records=records), nodes=nodes,
                research_plan=dict(defined_at=EARLY, materiality_threshold=.05, materiality_basis="5% of normalized operating activity, explicit test threshold",
                                   businesses=[dict(name="core", weight=1, weight_basis="All operating activity", industry="nonfinancial", method="dcf",
                                                    routing_basis="Nonfinancial cash-generating business", economic_ids=["core-business"], drivers=sorted(DRIVERS["dcf"]))], rules=rules),
                evidence_gate=dict(status="pass", as_of=T, critical_missing=[], material_conflicts=[], drivers=drivers),
                scenarios=[dict(name="base", probability=1, probability_ref="scenario_probability",
                                segments=[dict(name="core", method="dcf", basis="enterprise", inputs=dict(explicit_fcff=[10], discount_rate=.1, terminal_growth=0),
                                               provenance={"explicit_fcff.0": "forecast", "discount_rate": "discount_rate", "terminal_growth": "terminal_growth"})],
                                equity_bridge=bridge, bridge_provenance={k: "bridge_" + k for k in bridge},
                                bridge_allocations={k: [] for k in bridge if k != "diluted_shares"})])


def add_holding(p):
    name = "investment"
    inputs = dict(intrinsic_equity_value=200, ownership=.4, tax_leakage=0, liquidity_discount=0)
    refs = {}
    for k, v in inputs.items():
        rid = "holding_" + k; refs[k] = rid
        p["ledger"]["records"].append(record(rid, k, v, unit_for(k, "CNY", "ones"), name))
        p["evidence_gate"]["drivers"].append(dict(name=k, business_line=name, scope="CN/product", record_ids=[rid], bounds_refs=[rid, rid], causal_ref=rid))
        p["research_plan"]["rules"][name + "/" + k] = dict(min_independent=1, min_primary=1, max_age_hours=24, min_coverage=.9, rationale="Synthetic test input")
    p["research_plan"]["businesses"][0]["weight"] = .5
    p["research_plan"]["businesses"].append(dict(name=name, weight=.5, weight_basis="half of fixture economic scope", industry="holding", method="holding", routing_basis="Unconsolidated investment", economic_ids=["underlying-investee"], drivers=list(inputs)))
    p["scenarios"][0]["segments"].append(dict(name=name, method="holding", basis="equity", inputs=inputs, provenance=refs))


class ContractTests(unittest.TestCase):
    def test_amount_scale_normalizes_per_share(self):
        p = fixture()
        p["amount_unit"] = "millions"
        for r in p["ledger"]["records"]:
            if r["unit"] == "CNY:ones":
                r["unit"] = "CNY:millions"
        for n in p["nodes"].values():
            n["unit"] = "CNY:millions"
        result = evaluate(p)
        self.assertAlmostEqual(result["probability_weighted_equity_value"], 100)
        self.assertAlmostEqual(result["probability_weighted_per_share_value"], 10000000)
        self.assertEqual(result["per_share_unit"], "CNY/share")

    def test_unknown_amount_scale_rejected(self):
        p = fixture(); p["amount_unit"] = "wan"
        self.rejected(p, "unsupported amount_unit")

    def rejected(self, p, pattern):
        with self.assertRaisesRegex(InputError, pattern):
            evaluate(p)

    def test_end_to_end_operating_bridge(self):
        p = fixture()
        # Ten units at three, less cash costs 10, WC 5, capex 5 = FCFF 10.
        # Flat perpetuity at 10% = 100; ten shares = 10 each.
        result = evaluate(p)
        self.assertAlmostEqual(result["probability_weighted_equity_value"], 100)
        self.assertAlmostEqual(result["probability_weighted_per_share_value"], 10)
        self.assertEqual(len(result["evidence_audit"]["coverage"]), 8)
        self.assertIn("forecast", result["evidence_audit"]["assumptions"])

    def test_same_day_future_leak(self):
        p = fixture()
        p["ledger"]["records"][0]["available_at"] = "2026-01-02T13:00:00Z"
        self.rejected(p, "look-ahead")

    def test_timezone_equivalence(self):
        p = fixture()
        p["ledger"]["as_of"] = "2026-01-02T20:00:00+08:00"
        self.assertAlmostEqual(evaluate(p)["probability_weighted_equity_value"], 100)

    def test_timezone_can_reveal_future(self):
        p = fixture()
        p["ledger"]["records"][0]["available_at"] = "2026-01-02T10:00:00-05:00"
        self.rejected(p, "look-ahead")

    def test_date_only_is_not_an_intraday_cutoff(self):
        p = fixture(); p["as_of"] = "2026-01-02"
        self.rejected(p, "timezone")

    def test_revision_after_cutoff(self):
        p = fixture(); r = p["ledger"]["records"][0]
        r.update(vintage_at="2026-01-03T09:00:00Z", available_at="2026-01-03T09:00:00Z", collected_at="2026-01-03T10:00:00Z")
        self.rejected(p, "look-ahead")

    def test_archived_vintage_collected_later_is_valid(self):
        p = fixture(); p["ledger"]["records"][0]["collected_at"] = "2026-02-02T09:00:00Z"
        self.assertAlmostEqual(evaluate(p)["probability_weighted_equity_value"], 100)

    def test_missing_snapshot_is_rejected(self):
        p = fixture(); p["ledger"]["records"][0]["snapshot_reference"] = ""
        self.rejected(p, "snapshot_reference")

    def test_nonexistent_cross_check(self):
        p = fixture(); p["ledger"]["records"][0]["cross_checks"] = ["ghost"]
        self.rejected(p, "cross_checks")

    def test_nonexistent_provenance(self):
        p = fixture(); p["scenarios"][0]["segments"][0]["provenance"]["explicit_fcff.0"] = "ghost"
        self.rejected(p, "unresolved provenance")

    def test_source_value_disagrees(self):
        p = fixture(); p["scenarios"][0]["segments"][0]["inputs"]["explicit_fcff"][0] = 11
        self.rejected(p, "disagrees")

    def test_wrong_business_support(self):
        p = fixture(); p["nodes"]["forecast"]["business_line"] = "other"
        self.rejected(p, "mismapped|support")

    def test_currency_mismatch(self):
        p = fixture(); p["currency"] = "USD"
        self.rejected(p, "unit/currency")

    def test_missing_nested_provenance(self):
        p = fixture(); p["scenarios"][0]["segments"][0]["provenance"] = {"explicit_fcff": "forecast", "discount_rate": "discount_rate", "terminal_growth": "terminal_growth"}
        self.rejected(p, "numeric leaf")

    def test_provenance_cycle(self):
        p = fixture(); p["nodes"]["forecast"]["evidence_refs"] = ["forecast"]
        self.rejected(p, "cyclic")

    def test_market_contamination_even_via_assumption(self):
        p = fixture(); p["ledger"]["records"][0]["source_kind"] = "market"
        self.rejected(p, "market information")

    def test_omitted_material_driver(self):
        p = fixture(); p["evidence_gate"]["drivers"].pop()
        self.rejected(p, "missing from gate")

    def test_declaring_no_drivers_in_plan_cannot_pass(self):
        p = fixture(); p["research_plan"]["businesses"][0]["drivers"] = []
        self.rejected(p, "drivers omitted")

    def test_unvalued_business_cannot_disappear(self):
        p = fixture(); b = copy.deepcopy(p["research_plan"]["businesses"][0]); b.update(name="other", weight=.01, economic_ids=["other"])
        p["research_plan"]["businesses"][0]["weight"] = .99
        p["research_plan"]["businesses"].append(b)
        self.rejected(p, "full business inventory")

    def test_source_count_is_computed_not_claimed(self):
        p = fixture(); p["research_plan"]["rules"]["core/quantity"]["min_independent"] = 2
        p["evidence_gate"]["drivers"][0]["independent_source_count"] = 999
        self.rejected(p, "thresholds fail")

    def test_reprints_not_independent(self):
        p = fixture(); r = copy.deepcopy(p["ledger"]["records"][0]); r.update(record_id="reprint", source_publisher="Different news website")
        p["ledger"]["records"].append(r)
        next(d for d in p["evidence_gate"]["drivers"] if d["name"] == "quantity")["record_ids"].append("reprint")
        p["research_plan"]["rules"]["core/quantity"]["min_independent"] = 2
        self.rejected(p, "thresholds fail")

    def test_coverage_and_staleness(self):
        for field, value, error in [("coverage", .5, "coverage threshold"), ("observed_at", "2025-01-01T00:00:00Z", "stale")]:
            with self.subTest(field=field):
                p = fixture(); p["ledger"]["records"][0][field] = value
                self.rejected(p, error)

    def test_conflict_not_hidden_by_pass(self):
        p = fixture(); r = copy.deepcopy(p["ledger"]["records"][0]); r.update(record_id="contradiction", status="conflicted")
        p["ledger"]["records"].append(r)
        self.rejected(p, "unresolved material conflict")

    def test_unknown_assumption_only_conditional(self):
        p = fixture(); p["nodes"]["forecast"]["bounded_by_evidence"] = False
        self.rejected(p, "conditional analysis")
        p["analysis_mode"] = "conditional"
        result = evaluate(p)
        self.assertEqual(result["evidence_audit"]["computed_status"], "conditional")

    def test_unsupported_industry_no_generic_fallback(self):
        for industry in ("insurance", "reit", "biotech", "mining"):
            p = fixture(); p["research_plan"]["businesses"][0]["industry"] = industry
            self.rejected(p, "method gap")

    def test_duplicate_economic_ownership(self):
        p = fixture(); p["research_plan"]["businesses"][0]["economic_ids"].append("core-business")
        self.rejected(p, "double counted")

    def test_bridge_reconciles_and_is_applied_once(self):
        p = fixture(); s = p["scenarios"][0]
        s["equity_bridge"]["debt"] = 20
        next(r for r in p["ledger"]["records"] if r["record_id"] == "bridge_debt")["value"] = 20
        s["bridge_allocations"]["debt"] = [dict(id="loan-1", owner="core", ref="bridge_debt")]
        self.assertAlmostEqual(evaluate(p)["probability_weighted_equity_value"], 80)
        s["bridge_allocations"]["debt"].append(dict(id="loan-1", owner="core", ref="bridge_debt"))
        self.rejected(p, "duplicate economic")

    def test_unknown_input_not_zero(self):
        p = fixture(); p["scenarios"][0]["equity_bridge"]["cash"] = None
        self.rejected(p, "null")

    def test_mixed_enterprise_and_equity_bridge(self):
        p = fixture(); add_holding(p)
        # Core EV 100 + 40% * investee EQUITY 200 = 180; no second investee debt deduction.
        self.assertAlmostEqual(evaluate(p)["probability_weighted_equity_value"], 180)
        s = p["scenarios"][0]; s["equity_bridge"]["debt"] = 20
        next(r for r in p["ledger"]["records"] if r["record_id"] == "bridge_debt")["value"] = 20
        s["bridge_allocations"]["debt"] = [dict(id="investee-loan", owner="investment", ref="bridge_debt")]
        self.rejected(p, "direct equity segment")
        s["bridge_allocations"]["debt"][0]["owner"] = "__parent__"
        self.assertAlmostEqual(evaluate(p)["probability_weighted_equity_value"], 160)

    def test_minority_interest_must_have_consolidated_owner(self):
        p = fixture(); s = p["scenarios"][0]
        s["equity_bridge"]["minority_interest"] = 10
        next(r for r in p["ledger"]["records"] if r["record_id"] == "bridge_minority_interest")["value"] = 10
        s["bridge_allocations"]["minority_interest"] = [dict(id="minority-claim", owner="core", ref="bridge_minority_interest")]
        self.assertAlmostEqual(evaluate(p)["probability_weighted_equity_value"], 90)
        s["bridge_allocations"]["minority_interest"][0]["owner"] = "__parent__"
        self.rejected(p, "minority claim")

    def test_nested_parameters_require_individual_support(self):
        p = fixture(); audit = Audit(p)
        inputs = dict(outcomes=[dict(name="success", probability=1, path=["success"], conditional_probabilities=[1], value_at_resolution=121, years=2, discount_rate=.1, incremental_investment_pv=10)])
        refs = {}
        for i, (path, value) in enumerate(leaves(inputs)):
            rid = "nested_" + str(i); refs[path] = rid
            r = record(rid, driver_for(path), value, unit_for(path, "CNY", "ones"), "project")
            audit.records[rid] = r
        audit.bind(inputs, refs, "project")
        refs["outcomes.0.years"] = "ghost"
        with self.assertRaisesRegex(ContractError, "unresolved"):
            audit.bind(inputs, refs, "project")

    def test_reflexivity_handoff_separate_from_base(self):
        p = fixture()
        inputs = dict(incremental_fcff=[3], discount_rate=.1, terminal_growth=0, execution_probability=1,
                      failure_value=0, failure_years=1, equity_proceeds=20, debt_proceeds=0,
                      investment_now=20, issuance_costs=0, debt_claim_pv=0, old_shares=10, new_shares=5)
        refs = {}
        for i, (path, v) in enumerate(leaves(inputs)):
            rid = "finance_" + str(i); refs[path] = rid
            p["ledger"]["records"].append(record(rid, driver_for(path), v, unit_for(path, "CNY", "ones"), "__financing__"))
        p["financing_analysis"] = dict(inputs=inputs, provenance=refs, scope_basis="New project, cash raised and claims all excluded from base")
        result = evaluate(p)
        self.assertAlmostEqual(result["probability_weighted_equity_value"], 100)
        self.assertAlmostEqual(result["financing_analysis"][0]["original_holders_increment"], -13.3333333333333)
        inputs["old_shares"] = 11
        self.rejected(p, "disagrees|old shares")

    def test_raw_framework_order_cannot_be_cash_flow(self):
        p = fixture(); p["nodes"].pop("forecast")
        p["ledger"]["records"].append(record("forecast", "cash_flow", 10, "CNY:ones"))
        p["ledger"]["records"][-1]["supply_chain_stage"] = "framework_order"
        d = next(d for d in p["evidence_gate"]["drivers"] if d["name"] == "cash_flow")
        d["record_ids"] = ["forecast"]
        self.rejected(p, "unconverted operational stage")

    def test_anonymous_formula_constant_rejected(self):
        p = fixture(); p["nodes"]["fcff"]["args"][1] = 0
        self.rejected(p, "no anonymous constants")

    def test_market_top_level_rejected(self):
        p = fixture(); p["current_share_price"] = 100
        self.rejected(p, "top-level")

    def test_bad_types_fail_closed(self):
        for bad in [None, [], {"schema_version": 2}]:
            with self.assertRaises(InputError): evaluate(bad)

    def test_reverse_has_no_effect_on_forward(self):
        p = fixture(); baseline = evaluate(p)["probability_weighted_equity_value"]
        reverse = dict(current_enterprise_value=144.621188998361, base_fcff=10, discount_rate=.1, terminal_growth=.02, years=5, growth_search_low=-.5, growth_search_high=.5)
        refs = {}
        for k, v in reverse.items():
            rid = "reverse_" + k; refs[k] = rid
            r = record(rid, k, v, unit_for(k, "CNY", "ones"), "__reverse__")
            r["source_kind"] = "market"; p["ledger"]["records"].append(r)
        p["reverse_valuation"] = dict(inputs=reverse, provenance=refs)
        output = evaluate(p)
        self.assertEqual(output["probability_weighted_equity_value"], baseline)
        self.assertAlmostEqual(output["reverse_valuation"]["implied_constant_growth"], .05)

    def test_cli_handoff_and_nonzero_rejection(self):
        scripts = Path(__file__).resolve().parent
        intake = scripts.parents[1] / "fundamental-signal-intake" / "scripts" / "validate_ledger.py"
        with tempfile.TemporaryDirectory() as tmp:
            p = fixture(); ledger = Path(tmp) / "ledger.json"; valuation = Path(tmp) / "valuation.json"
            ledger.write_text(json.dumps(p["ledger"]), encoding="utf-8")
            valuation.write_text(json.dumps(p), encoding="utf-8")
            for script, file in [(intake, ledger), (scripts / "valuation_engine.py", valuation)]:
                result = subprocess.run([sys.executable, "-B", str(script), str(file)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            p["scenarios"][0]["segments"][0]["provenance"]["explicit_fcff.0"] = "missing"
            valuation.write_text(json.dumps(p), encoding="utf-8")
            result = subprocess.run([sys.executable, "-B", str(scripts / "valuation_engine.py"), str(valuation)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("equity_value", result.stdout)


class IndependentFormulaTests(unittest.TestCase):
    def test_residual_income_growth_uses_next_opening_book(self):
        # B0=100, NI1=12, B1=110. RI1=2, RI2=(.15-.10)*110=5.5.
        # PV = 100 + 2/1.1 + (5.5/.08)/1.1 = 164.318181818.
        actual = residual_income(dict(opening_book_value=100, forecast_net_income=[12], forecast_ending_book_values=[110], cost_of_equity=.1, terminal_roe=.15, terminal_growth=.02))
        self.assertAlmostEqual(actual, 164.3181818181818)

    def test_reject_roic_in_equity_growth_model(self):
        with self.assertRaises(InputError):
            midcycle(dict(normalized_net_income=10, reinvestment_rate=.2, incremental_roic=.15, cost_of_equity=.1))

    def test_asset_delay(self):
        actual = asset_value(dict(assets=[dict(name="land", fair_value=121, realizability_probability=1, tax_leakage=0, haircut=0, years=2, discount_rate=.1)]))
        self.assertAlmostEqual(actual, 100)

    def test_conditional_tree_timing_and_failure_residual(self):
        outcomes = [
            dict(name="approved", probability=.3, path=["technical_success", "customer_success"], conditional_probabilities=[.6, .5], value_at_resolution=121, years=2, discount_rate=.1, incremental_investment_pv=10),
            dict(name="customer_failure", probability=.3, path=["technical_success", "customer_failure"], conditional_probabilities=[.6, .5], value_at_resolution=11, years=1, discount_rate=.1, incremental_investment_pv=5),
            dict(name="technical_failure", probability=.4, path=["technical_failure"], conditional_probabilities=[.4], value_at_resolution=0, years=0, discount_rate=.1, incremental_investment_pv=5)]
        self.assertAlmostEqual(option_value(dict(outcomes=outcomes)), 26.5)
        outcomes[0]["conditional_probabilities"] = [.5, .6]
        with self.assertRaisesRegex(InputError, "inconsistent"):
            option_value(dict(outcomes=outcomes))

    def test_financing_dilution_is_per_original_holder(self):
        # Base=100. Raise 20 issuing 5 shares; invest 20 into a project PV=30.
        # Post value=130, original fraction=10/15, original value=86 2/3.
        inputs = dict(incremental_fcff=[3], discount_rate=.1, terminal_growth=0, execution_probability=1,
                      failure_value=0, failure_years=1, equity_proceeds=20, debt_proceeds=0,
                      investment_now=20, issuance_costs=0, debt_claim_pv=0, old_shares=10, new_shares=5)
        result = reflexivity(inputs, 100)
        self.assertAlmostEqual(result["project_npv"], 10)
        self.assertAlmostEqual(result["original_holders_increment"], -13.3333333333333)
        inputs["new_shares"] = 0
        with self.assertRaises(InputError): reflexivity(inputs, 100)


if __name__ == "__main__":
    unittest.main()

