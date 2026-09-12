#!/usr/bin/env python3
"""Deterministic, evidence-gated valuation engine.

No financial defaults are permitted. Every numeric input must be supplied and
mapped to provenance. Forward valuation never reads market price; reverse DCF
is a separate optional calculation.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any
from evidence_contract import audit, ContractError, leaves, AMOUNT_SCALES


class InputError(ValueError):
    pass


def require(mapping: dict[str, Any], keys: list[str], context: str) -> None:
    if not isinstance(mapping, dict):
        raise InputError(f"{context}: must be an object")
    missing = [key for key in keys if key not in mapping]
    if missing:
        raise InputError(f"{context}: missing required fields: {', '.join(missing)}")


def require_exact(mapping: dict[str, Any], keys: list[str], context: str) -> None:
    require(mapping, keys, context)
    unexpected = sorted(set(mapping) - set(keys))
    if unexpected:
        raise InputError(f"{context}: unexpected fields are not silently ignored: {', '.join(unexpected)}")


def number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise InputError(f"{context}: must be a finite number")
    return float(value)


def probability(value: Any, context: str) -> float:
    result = number(value, context)
    if result < 0 or result > 1:
        raise InputError(f"{context}: probability must be in [0, 1]")
    return result


def check_rate_pair(discount_rate: float, terminal_growth: float, context: str) -> None:
    if discount_rate <= terminal_growth:
        raise InputError(f"{context}: discount rate must exceed terminal growth")
    if discount_rate <= -1 or terminal_growth <= -1:
        raise InputError(f"{context}: rates must be greater than -100%")


def require_provenance(inputs: dict[str, Any], provenance: Any, context: str) -> None:
    if not isinstance(provenance, dict):
        raise InputError(f"{context}: provenance must be an object")
    missing = []
    for key, _ in leaves(inputs):
        refs = provenance.get(key)
        invalid_list = isinstance(refs, list) and (
            not refs or any(not isinstance(ref, str) or not ref.strip() for ref in refs)
        )
        if (
            not isinstance(refs, (str, list))
            or (isinstance(refs, str) and not refs.strip())
            or invalid_list
        ):
            missing.append(key)
    if missing:
        raise InputError(f"{context}: missing provenance for: {', '.join(missing)}")


def pv_explicit(flows: list[Any], discount_rate: float, context: str) -> tuple[float, float]:
    if not isinstance(flows, list) or not flows:
        raise InputError(f"{context}: cash flows must be a non-empty list")
    values = [number(value, f"{context}[{index}]") for index, value in enumerate(flows)]
    present = sum(value / ((1 + discount_rate) ** year) for year, value in enumerate(values, 1))
    return present, values[-1]


def dcf(inputs: dict[str, Any]) -> float:
    require_exact(inputs, ["explicit_fcff", "discount_rate", "terminal_growth"], "dcf")
    rate = number(inputs["discount_rate"], "dcf.discount_rate")
    growth = number(inputs["terminal_growth"], "dcf.terminal_growth")
    check_rate_pair(rate, growth, "dcf")
    present, last = pv_explicit(inputs["explicit_fcff"], rate, "dcf.explicit_fcff")
    years = len(inputs["explicit_fcff"])
    terminal = last * (1 + growth) / (rate - growth)
    return present + terminal / ((1 + rate) ** years)


def residual_income(inputs: dict[str, Any]) -> float:
    require_exact(inputs, ["opening_book_value", "forecast_net_income", "forecast_ending_book_values", "cost_of_equity", "terminal_roe", "terminal_growth"], "residual_income")
    opening = number(inputs["opening_book_value"], "residual_income.opening_book_value")
    incomes = inputs["forecast_net_income"]
    books = inputs["forecast_ending_book_values"]
    if not isinstance(incomes, list) or not incomes or not isinstance(books, list) or len(incomes) != len(books):
        raise InputError("residual_income: forecast lists must be non-empty and have equal length")
    rate = number(inputs["cost_of_equity"], "residual_income.cost_of_equity")
    growth = number(inputs["terminal_growth"], "residual_income.terminal_growth")
    terminal_roe = number(inputs["terminal_roe"], "residual_income.terminal_roe")
    check_rate_pair(rate, growth, "residual_income")
    value = opening
    begin_book = opening
    for year, (income_raw, end_book_raw) in enumerate(zip(incomes, books), 1):
        income = number(income_raw, f"residual_income.forecast_net_income[{year - 1}]")
        end_book = number(end_book_raw, f"residual_income.forecast_ending_book_values[{year - 1}]")
        value += (income - rate * begin_book) / ((1 + rate) ** year)
        begin_book = end_book
    # RI[n+1] uses B[n] as its OPENING book. Growth starts in RI[n+2].
    residual_next = (terminal_roe - rate) * begin_book
    value += residual_next / (rate - growth) / ((1 + rate) ** len(incomes))
    return value


def midcycle(inputs: dict[str, Any]) -> float:
    require_exact(inputs, ["normalized_net_income", "reinvestment_rate", "incremental_roe", "cost_of_equity"], "midcycle")
    income = number(inputs["normalized_net_income"], "midcycle.normalized_net_income")
    reinvestment = probability(inputs["reinvestment_rate"], "midcycle.reinvestment_rate")
    roic = number(inputs["incremental_roe"], "midcycle.incremental_roe")
    cost = number(inputs["cost_of_equity"], "midcycle.cost_of_equity")
    growth = reinvestment * roic
    check_rate_pair(cost, growth, "midcycle")
    distributable = income * (1 - reinvestment)
    return distributable * (1 + growth) / (cost - growth)


def holding(inputs: dict[str, Any]) -> float:
    require_exact(inputs, ["intrinsic_equity_value", "ownership", "tax_leakage", "liquidity_discount"], "holding")
    value = number(inputs["intrinsic_equity_value"], "holding.intrinsic_equity_value")
    own = probability(inputs["ownership"], "holding.ownership")
    tax = probability(inputs["tax_leakage"], "holding.tax_leakage")
    discount = probability(inputs["liquidity_discount"], "holding.liquidity_discount")
    return value * own * (1 - tax) * (1 - discount)


def option_value(inputs: dict[str, Any]) -> float:
    require_exact(inputs, ["outcomes"], "option")
    outcomes = inputs["outcomes"]
    if not isinstance(outcomes, list) or not outcomes:
        raise InputError("option.outcomes must be a non-empty list")
    total_probability = 0.0
    total = 0.0
    paths = {}
    edges = {}
    for index, outcome in enumerate(outcomes):
        context = f"option.outcomes[{index}]"
        if not isinstance(outcome, dict):
            raise InputError(f"{context}: must be an object")
        require_exact(outcome, ["name", "probability", "path", "conditional_probabilities", "value_at_resolution", "years", "discount_rate", "incremental_investment_pv"], context)
        prob = probability(outcome["probability"], f"{context}.probability")
        path = outcome["path"]
        conditional = outcome["conditional_probabilities"]
        if not isinstance(path, list) or not path or not all(isinstance(x, str) and x.strip() for x in path) or not isinstance(conditional, list) or len(path) != len(conditional):
            raise InputError(f"{context}: stage path and conditional probabilities required")
        path = tuple(path)
        if path in paths:
            raise InputError("option: duplicate terminal outcome path")
        paths[path] = prob
        probabilities = [probability(x, context) for x in conditional]
        if not math.isclose(math.prod(probabilities), prob, abs_tol=1e-10):
            raise InputError("option: joint probability differs from conditional product")
        for depth, conditional_prob in enumerate(probabilities):
            edge = path[:depth + 1]
            if edge in edges and not math.isclose(edges[edge], conditional_prob, abs_tol=1e-10):
                raise InputError("option: inconsistent conditional probability on shared stage")
            edges[edge] = conditional_prob
        years = number(outcome["years"], f"{context}.years")
        if years < 0:
            raise InputError(f"{context}.years must be non-negative")
        rate = number(outcome["discount_rate"], f"{context}.discount_rate")
        if rate <= -1:
            raise InputError(f"{context}.discount_rate must be greater than -100%")
        value = number(outcome["value_at_resolution"], f"{context}.value_at_resolution")
        investment = number(outcome["incremental_investment_pv"], f"{context}.incremental_investment_pv")
        if investment < 0:
            raise InputError("option: investment PV must be nonnegative and conditional on this path")
        total_probability += prob
        total += prob * (value / ((1 + rate) ** years) - investment)
    if not math.isclose(total_probability, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise InputError("option outcome probabilities must sum to 1")
    for path in paths:
        if any(other != path and other[:len(path)] == path for other in paths):
            raise InputError("option: terminal outcome overlaps a descendant outcome")
    for parent in {edge[:-1] for edge in edges}:
        if not math.isclose(sum(v for edge, v in edges.items() if edge[:-1] == parent), 1, abs_tol=1e-10):
            raise InputError("option: each stage's outgoing conditional probabilities must sum to 1")
    return total


def asset_value(inputs: dict[str, Any]) -> float:
    require_exact(inputs, ["assets"], "asset")
    assets = inputs["assets"]
    if not isinstance(assets, list) or not assets:
        raise InputError("asset.assets must be a non-empty list")
    total = 0.0
    for index, item in enumerate(assets):
        context = f"asset.assets[{index}]"
        require_exact(item, ["name", "fair_value", "realizability_probability", "tax_leakage", "haircut", "years", "discount_rate"], context)
        years = number(item["years"], context + ".years")
        rate = number(item["discount_rate"], context + ".discount_rate")
        if years < 0 or rate <= -1:
            raise InputError("asset: invalid disposal time or discount rate")
        total += number(item["fair_value"], f"{context}.fair_value") * probability(item["realizability_probability"], f"{context}.realizability_probability") * (1 - probability(item["tax_leakage"], f"{context}.tax_leakage")) * (1 - probability(item["haircut"], f"{context}.haircut")) / (1 + rate) ** years
    return total


def reflexivity(inputs: dict[str, Any], base_equity: float) -> dict[str, float]:
    require_exact(inputs, ["incremental_fcff", "discount_rate", "terminal_growth", "execution_probability", "failure_value", "failure_years", "equity_proceeds", "debt_proceeds", "investment_now", "issuance_costs", "debt_claim_pv", "old_shares", "new_shares"], "reflexivity")
    rate = number(inputs["discount_rate"], "reflexivity.discount_rate")
    growth = number(inputs["terminal_growth"], "reflexivity.terminal_growth")
    check_rate_pair(rate, growth, "reflexivity")
    present, last = pv_explicit(inputs["incremental_fcff"], rate, "reflexivity.incremental_fcff")
    years = len(inputs["incremental_fcff"])
    terminal = last * (1 + growth) / (rate - growth) / ((1 + rate) ** years)
    execution = probability(inputs["execution_probability"], "reflexivity.execution_probability")
    other = {key: number(inputs[key], "reflexivity." + key) for key in ["failure_value", "failure_years", "equity_proceeds", "debt_proceeds", "investment_now", "issuance_costs", "debt_claim_pv", "old_shares", "new_shares"]}
    if any(v < 0 for v in other.values()) or other["old_shares"] <= 0:
        raise InputError("reflexivity: invalid proceeds, costs, time or share counts")
    if (other["equity_proceeds"] > 0) != (other["new_shares"] > 0):
        raise InputError("reflexivity: equity issuance proceeds and new shares must agree")
    if (other["debt_proceeds"] > 0) != (other["debt_claim_pv"] > 0):
        raise InputError("reflexivity: debt proceeds and new debt claim must agree")
    project_pv = execution * (present + terminal) + (1 - execution) * other["failure_value"] / (1 + rate) ** other["failure_years"]
    post_equity = base_equity + other["equity_proceeds"] + other["debt_proceeds"] - other["issuance_costs"] - other["investment_now"] + project_pv - other["debt_claim_pv"]
    post_shares = other["old_shares"] + other["new_shares"]
    old_value = post_equity * other["old_shares"] / post_shares
    return {"project_pv": project_pv, "project_npv": project_pv - other["investment_now"], "post_financing_equity": post_equity, "post_financing_per_share": post_equity / post_shares, "original_holders_value": old_value, "original_holders_increment": old_value - base_equity}


METHODS = {
    "dcf": (dcf, "enterprise"),
    "residual_income": (residual_income, "equity"),
    "midcycle": (midcycle, "equity"),
    "holding": (holding, "equity"),
    "option": (option_value, None),
    "asset": (asset_value, "enterprise"),
}


def validate_gate(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate the full executable contract; caller-written statuses are insufficient."""
    try:
        return audit(payload)[1]
    except ContractError as exc:
        raise InputError(str(exc)) from exc


def value_segment(segment: dict[str, Any], context: str) -> dict[str, Any]:
    require(segment, ["name", "method", "basis", "inputs", "provenance"], context)
    method = segment["method"]
    if method not in METHODS:
        raise InputError(f"{context}: unsupported method {method!r}")
    inputs = segment["inputs"]
    if not isinstance(inputs, dict):
        raise InputError(f"{context}.inputs must be an object")
    require_provenance(inputs, segment["provenance"], context)
    function, fixed_basis = METHODS[method]
    basis = segment["basis"]
    if basis not in {"enterprise", "equity"}:
        raise InputError(f"{context}.basis must be enterprise or equity")
    if fixed_basis and basis != fixed_basis:
        raise InputError(f"{context}: method {method} requires {fixed_basis} basis")
    return {"name": segment["name"], "method": method, "basis": basis, "value": function(inputs)}


BRIDGE_KEYS = ["cash", "debt", "lease_liabilities", "minority_interest", "non_operating_assets", "contingent_liabilities", "diluted_shares"]


def value_scenario(scenario: dict[str, Any], index: int) -> dict[str, Any]:
    context = f"scenarios[{index}]"
    require(scenario, ["name", "probability", "segments", "equity_bridge", "bridge_provenance"], context)
    prob = probability(scenario["probability"], f"{context}.probability")
    segments = scenario["segments"]
    if not isinstance(segments, list) or not segments:
        raise InputError(f"{context}.segments must be a non-empty list")
    results = [value_segment(item, f"{context}.segments[{i}]") for i, item in enumerate(segments)]
    bridge = scenario["equity_bridge"]
    if not isinstance(bridge, dict):
        raise InputError(f"{context}.equity_bridge must be an object")
    require(bridge, BRIDGE_KEYS, f"{context}.equity_bridge")
    require_provenance({key: bridge[key] for key in BRIDGE_KEYS}, scenario["bridge_provenance"], f"{context}.equity_bridge")
    b = {key: number(bridge[key], f"{context}.equity_bridge.{key}") for key in BRIDGE_KEYS}
    if b["diluted_shares"] <= 0:
        raise InputError(f"{context}: diluted_shares must be positive")
    enterprise = sum(item["value"] for item in results if item["basis"] == "enterprise")
    direct_equity = sum(item["value"] for item in results if item["basis"] == "equity")
    equity = enterprise - b["debt"] - b["lease_liabilities"] - b["minority_interest"] + b["cash"] + b["non_operating_assets"] - b["contingent_liabilities"] + direct_equity
    return {"name": scenario["name"], "probability": prob, "segments": results, "enterprise_segment_value": enterprise, "direct_equity_segment_value": direct_equity, "equity_value": equity, "per_share_value": equity / b["diluted_shares"]}


def growing_dcf(base: float, growth: float, rate: float, terminal_growth: float, years: int) -> float:
    flow = base
    present = 0.0
    for year in range(1, years + 1):
        flow *= 1 + growth
        present += flow / ((1 + rate) ** year)
    terminal = flow * (1 + terminal_growth) / (rate - terminal_growth)
    return present + terminal / ((1 + rate) ** years)


def reverse_dcf(inputs: dict[str, Any], provenance: Any) -> dict[str, float]:
    required = ["current_enterprise_value", "base_fcff", "discount_rate", "terminal_growth", "years", "growth_search_low", "growth_search_high"]
    require_exact(inputs, required, "reverse_valuation")
    require_provenance(inputs, provenance, "reverse_valuation")
    target = number(inputs["current_enterprise_value"], "reverse.current_enterprise_value")
    base = number(inputs["base_fcff"], "reverse.base_fcff")
    rate = number(inputs["discount_rate"], "reverse.discount_rate")
    terminal_growth = number(inputs["terminal_growth"], "reverse.terminal_growth")
    years_raw = number(inputs["years"], "reverse.years")
    years = int(years_raw)
    if years <= 0 or years != years_raw or base <= 0 or target <= 0:
        raise InputError("reverse valuation requires positive target/base and an integer years > 0")
    check_rate_pair(rate, terminal_growth, "reverse_valuation")
    low = number(inputs["growth_search_low"], "reverse.growth_search_low")
    high = number(inputs["growth_search_high"], "reverse.growth_search_high")
    if low <= -1 or high <= low:
        raise InputError("reverse valuation requires growth_search_low > -100% and growth_search_high > growth_search_low")
    if not (growing_dcf(base, low, rate, terminal_growth, years) <= target <= growing_dcf(base, high, rate, terminal_growth, years)):
        raise InputError("reverse valuation target is outside the supported growth search range")
    for _ in range(200):
        middle = (low + high) / 2
        if growing_dcf(base, middle, rate, terminal_growth, years) < target:
            low = middle
        else:
            high = middle
    implied = (low + high) / 2
    return {"implied_constant_growth": implied, "reconstructed_enterprise_value": growing_dcf(base, implied, rate, terminal_growth, years)}


def _evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    try:
        checker, evidence_report = audit(payload)
    except ContractError as exc:
        raise InputError(str(exc)) from exc
    scenarios = payload["scenarios"]
    if not isinstance(scenarios, list) or not scenarios:
        raise InputError("scenarios must be a non-empty list")
    results = [value_scenario(item, index) for index, item in enumerate(scenarios)]
    scale = AMOUNT_SCALES[payload["amount_unit"]]
    for item in results:
        item["per_share_value"] *= scale
    total_probability = sum(item["probability"] for item in results)
    if not math.isclose(total_probability, 1.0, rel_tol=1e-9, abs_tol=1e-9):
        raise InputError("scenario probabilities must sum to 1")
    output: dict[str, Any] = {
        "as_of": payload["as_of"],
        "currency": payload["currency"],
        "amount_unit": payload["amount_unit"],
        "per_share_unit": payload["currency"] + "/share",
        "evidence_audit": evidence_report,
        "scenarios": results,
        "probability_weighted_equity_value": sum(item["probability"] * item["equity_value"] for item in results),
        "probability_weighted_per_share_value": sum(item["probability"] * item["per_share_value"] for item in results),
    }
    reverse = payload.get("reverse_valuation")
    if reverse is not None:
        if not isinstance(reverse, dict):
            raise InputError("reverse_valuation must be null or an object")
        require(reverse, ["inputs", "provenance"], "reverse_valuation")
        try:
            checker.bind(reverse["inputs"], reverse["provenance"], "__reverse__", forward=False)
        except ContractError as exc:
            raise InputError(str(exc)) from exc
        output["reverse_valuation"] = reverse_dcf(reverse["inputs"], reverse["provenance"])
    financing = payload.get("financing_analysis")
    if financing is not None:
        require(financing, ["inputs", "provenance", "scope_basis"], "financing_analysis")
        if not isinstance(financing["scope_basis"], str) or not financing["scope_basis"].strip():
            raise InputError("financing: explain exclusion of new project/proceeds/claims from base valuation")
        try:
            checker.bind(financing["inputs"], financing["provenance"], "__financing__", forward=False)
        except ContractError as exc:
            raise InputError(str(exc)) from exc
        for s in scenarios:
            if s["equity_bridge"]["diluted_shares"] != financing["inputs"]["old_shares"]:
                raise InputError("financing: old shares must equal base diluted shares")
        output["financing_analysis"] = [{"scenario": s["name"], **reflexivity(financing["inputs"], s["equity_value"])} for s in results]
        for item in output["financing_analysis"]:
            item["post_financing_per_share"] *= scale
    if reverse is not None or financing is not None:
        output["combined_input_audit"] = {
            "computed_status": "conditional" if checker.conditional else "pass",
            "assumptions": sorted(checker.assumptions),
            "unbounded_conditions": sorted(checker.conditional),
        }
    return output


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    """Public boundary: malformed input always fails with an actionable error."""
    try:
        return _evaluate(payload)
    except (ContractError, TypeError, KeyError, OverflowError, RecursionError) as exc:
        raise InputError(f"invalid or unsupported valuation input: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = evaluate(payload)
    except (OSError, json.JSONDecodeError, InputError, ContractError, TypeError, KeyError, OverflowError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

