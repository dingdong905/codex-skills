import math
import unittest

from valuation_engine import (
    InputError,
    asset_value,
    dcf,
    evaluate,
    holding,
    midcycle,
    option_value,
    reflexivity,
    residual_income,
    reverse_dcf,
)


def provenance(inputs):
    return {key: [f"source:{key}"] for key in inputs}


def payload(segment):
    from test_evidence_contract import fixture
    data = fixture()
    data["scenarios"][0]["segments"] = [segment]
    return data


class ValuationEngineTest(unittest.TestCase):
    def test_dcf_formula(self):
        value = dcf({"explicit_fcff": [10], "discount_rate": 0.10, "terminal_growth": 0.0})
        self.assertTrue(math.isclose(value, 100.0, rel_tol=1e-9))

    def test_rejects_missing_input(self):
        with self.assertRaises(InputError):
            dcf({"explicit_fcff": [10], "discount_rate": 0.10})

    def test_rejects_silently_ignored_input(self):
        with self.assertRaises(InputError):
            dcf({"explicit_fcff": [10], "discount_rate": 0.10, "terminal_growth": 0.0, "current_share_price": 99})

    def test_rejects_missing_provenance(self):
        inputs = {"explicit_fcff": [10], "discount_rate": 0.10, "terminal_growth": 0.0}
        segment = {"name": "core", "method": "dcf", "basis": "enterprise", "inputs": inputs, "provenance": {}}
        with self.assertRaises(InputError):
            evaluate(payload(segment))

    def test_rejects_blank_provenance_reference(self):
        inputs = {"explicit_fcff": [10], "discount_rate": 0.10, "terminal_growth": 0.0}
        segment = {
            "name": "core",
            "method": "dcf",
            "basis": "enterprise",
            "inputs": inputs,
            "provenance": {key: [""] for key in inputs},
        }
        with self.assertRaises(InputError):
            evaluate(payload(segment))

    def test_rejects_failed_gate(self):
        inputs = {"explicit_fcff": [10], "discount_rate": 0.10, "terminal_growth": 0.0}
        segment = {"name": "core", "method": "dcf", "basis": "enterprise", "inputs": inputs, "provenance": provenance(inputs)}
        data = payload(segment)
        data["evidence_gate"]["critical_missing"] = ["volume"]
        with self.assertRaises(InputError):
            evaluate(data)

    def test_rejects_unbounded_material_driver(self):
        inputs = {"explicit_fcff": [10], "discount_rate": 0.10, "terminal_growth": 0.0}
        segment = {"name": "core", "method": "dcf", "basis": "enterprise", "inputs": inputs, "provenance": provenance(inputs)}
        data = payload(segment)
        data["evidence_gate"]["drivers"][0]["bounds_refs"] = []
        with self.assertRaises(InputError):
            evaluate(data)

    def test_holding(self):
        value = holding({"intrinsic_equity_value": 100, "ownership": 0.4, "tax_leakage": 0.1, "liquidity_discount": 0.2})
        self.assertTrue(math.isclose(value, 28.8, rel_tol=1e-9))

    def test_residual_income_formula(self):
        value = residual_income({
            "opening_book_value": 100,
            "forecast_net_income": [12],
            "forecast_ending_book_values": [105],
            "cost_of_equity": 0.10,
            "terminal_roe": 0.10,
            "terminal_growth": 0.0,
        })
        self.assertTrue(math.isclose(value, 100 + 2 / 1.1, rel_tol=1e-9))

    def test_midcycle_formula(self):
        value = midcycle({
            "normalized_net_income": 10,
            "reinvestment_rate": 0.20,
            "incremental_roe": 0.15,
            "cost_of_equity": 0.10,
        })
        self.assertTrue(math.isclose(value, 8 * 1.03 / 0.07, rel_tol=1e-9))

    def test_option_formula_and_probability_closure(self):
        value = option_value({"outcomes": [
            {"name": "success", "probability": 0.25, "path": ["success"], "conditional_probabilities": [0.25], "value_at_resolution": 100, "years": 1, "discount_rate": 0.0, "incremental_investment_pv": 5},
            {"name": "failure", "probability": 0.75, "path": ["failure"], "conditional_probabilities": [0.75], "value_at_resolution": 0, "years": 1, "discount_rate": 0.0, "incremental_investment_pv": 0},
        ]})
        self.assertTrue(math.isclose(value, 23.75, rel_tol=1e-9))
        with self.assertRaises(InputError):
            option_value({"outcomes": [
                {"name": "incomplete", "probability": 0.8, "value_at_resolution": 1, "years": 1, "discount_rate": 0.0, "incremental_investment_pv": 0},
            ]})

    def test_asset_formula(self):
        value = asset_value({"assets": [{
            "name": "asset-a",
            "fair_value": 100,
            "realizability_probability": 0.8,
            "tax_leakage": 0.1,
            "haircut": 0.25,
            "years": 0, "discount_rate": 0,
        }]})
        self.assertTrue(math.isclose(value, 54.0, rel_tol=1e-9))

    def test_reflexivity_formula(self):
        value = reflexivity({
            "incremental_fcff": [10],
            "discount_rate": 0.10,
            "terminal_growth": 0.0,
            "execution_probability": 0.5,
            "failure_value": 0, "failure_years": 1,
            "equity_proceeds": 20, "debt_proceeds": 0, "investment_now": 20,
            "issuance_costs": 0, "debt_claim_pv": 0, "old_shares": 10, "new_shares": 2,
        }, 100)
        self.assertAlmostEqual(value["original_holders_increment"], 25)

    def test_reverse_dcf_recovers_growth(self):
        # Independently precomputed from five years of FCFF growing at 5%,
        # discounted at 10%, with a 2% perpetual-growth terminal value.
        inputs = {
            "current_enterprise_value": 144.621188998361,
            "base_fcff": 10,
            "discount_rate": 0.10,
            "terminal_growth": 0.02,
            "years": 5,
            "growth_search_low": -0.50,
            "growth_search_high": 0.50,
        }
        result = reverse_dcf(inputs, provenance(inputs))
        self.assertTrue(math.isclose(result["implied_constant_growth"], 0.05, abs_tol=1e-6))


if __name__ == "__main__":
    unittest.main()

