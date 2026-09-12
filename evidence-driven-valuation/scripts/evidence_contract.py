"""Executable v2 handoff. No network retrieval and no financial defaults.

Source support/independence labels remain auditable human assertions; numerical
resolution, timestamps, coverage and reference integrity are machine checked.
"""
from datetime import datetime, timezone
import importlib.util
import math
from pathlib import Path


class ContractError(ValueError):
    pass


def need(ok, message):
    if not ok:
        raise ContractError(message)


def numeric(x):
    return not isinstance(x, bool) and isinstance(x, (int, float)) and math.isfinite(x)


def instant(x):
    need(isinstance(x, str), "timestamp must be a string")
    try:
        t = datetime.fromisoformat(x.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("invalid timestamp") from exc
    need(t.tzinfo is not None and t.utcoffset() is not None, "timezone-aware timestamp required")
    return t.astimezone(timezone.utc)


def nonempty(x):
    return isinstance(x, str) and bool(x.strip())


def leaves(x, path=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, f"{path}.{k}" if path else k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, f"{path}.{i}")
    elif not isinstance(x, str):
        need(numeric(x), f"{path}: numeric leaf is null, boolean or non-finite")
        yield path, x


# Explicit routing whitelist, not an automatic fallback. Specialist modules
# that are not implemented fail even if the caller selects a generic method.
ROUTES = {
    "nonfinancial": {"dcf"}, "bank": {"residual_income"},
    "cyclical": {"midcycle", "dcf"}, "holding": {"holding"},
    "new_product": {"option"}, "asset_disposal": {"asset"},
}
DRIVERS = {
    "dcf": {"quantity", "price", "cost", "working_capital", "capex", "cash_flow", "discount_rate", "terminal_growth"},
    "midcycle": {"normalized_net_income", "reinvestment_rate", "incremental_roe", "cost_of_equity"},
    "residual_income": {"opening_book_value", "forecast_net_income", "forecast_ending_book_values", "cost_of_equity", "terminal_roe", "terminal_growth"},
    "holding": {"intrinsic_equity_value", "ownership", "tax_leakage", "liquidity_discount"},
    "option": {"probability", "value_at_resolution", "years", "discount_rate", "incremental_investment_pv"},
    "asset": {"fair_value", "realizability_probability", "tax_leakage", "haircut", "years", "discount_rate"},
}

AMOUNT_SCALES = {"ones": 1, "thousands": 1000, "millions": 1000000, "billions": 1000000000}


def driver_for(path):
    parts = [x for x in path.split(".") if not x.isdigit()]
    if parts[-1] == "conditional_probabilities":
        return "probability"
    return "cash_flow" if parts[0] == "explicit_fcff" else parts[-1]


def unit_for(path, currency, amount_unit):
    key = driver_for(path)
    if key in {"years", "failure_years"}:
        return "years"
    if key in {"diluted_shares", "old_shares", "new_shares"}:
        return "shares"
    if key in {"probability", "discount_rate", "terminal_growth", "cost_of_equity", "terminal_roe", "incremental_roe", "reinvestment_rate", "ownership", "tax_leakage", "liquidity_discount", "realizability_probability", "haircut", "execution_probability", "growth_search_low", "growth_search_high"}:
        return "ratio"
    return f"{currency}:{amount_unit}"


class Audit:
    def __init__(self, payload):
        self.p = payload
        need(isinstance(payload, dict) and payload.get("schema_version") == 2, "schema_version=2 required; legacy unverified inputs cannot be valued")
        allowed = {"schema_version", "as_of", "currency", "amount_unit", "analysis_mode", "scope_basis", "ledger", "nodes", "research_plan", "evidence_gate", "scenarios", "reverse_valuation", "financing_analysis"}
        need(set(payload) <= allowed, "unrecognized top-level inputs (including market price) cannot be silently ignored")
        self.cutoff = instant(payload.get("as_of"))
        need(nonempty(payload.get("currency")) and nonempty(payload.get("amount_unit")), "currency and amount_unit required")
        need(payload["amount_unit"] in AMOUNT_SCALES, "unsupported amount_unit; normalize explicitly to ones/thousands/millions/billions")
        need(payload.get("analysis_mode") in {"independent", "conditional"}, "analysis_mode required")
        need(nonempty(payload.get("scope_basis")), "scope_basis must explain full economic perimeter, including omitted exposures")
        ledger = payload.get("ledger")
        need(isinstance(ledger, dict), "embedded ledger required")
        need(instant(ledger.get("as_of")) == self.cutoff, "ledger cutoff mismatch")
        validator_path = Path(__file__).resolve().parents[2] / "fundamental-signal-intake" / "scripts" / "validate_ledger.py"
        need(validator_path.is_file(), "method dependency missing: fundamental-signal-intake validator")
        spec = importlib.util.spec_from_file_location("intake_contract_v2", validator_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        errors = module.validate(ledger)
        need(not errors, "ledger rejected: " + "; ".join(errors))
        self.records = {r["record_id"]: r for r in ledger["records"]}
        self.nodes = payload.get("nodes")
        need(isinstance(self.nodes, dict), "nodes registry required")
        need(not (set(self.records) & set(self.nodes)), "node and record IDs collide")
        self.cache = {}
        self.active = set()
        self.assumptions = set()
        self.conditional = set()
        self.coverage = []
        self.forward_refs = set()
        self.forward_used = set()

    def resolve(self, ref, forward=True):
        need(nonempty(ref), "reference must be a non-empty ID")
        key = (ref, forward)
        if forward:
            self.forward_used.add(ref)
        if key in self.cache:
            return self.cache[key]
        need(key not in self.active, f"cyclic provenance: {ref}")
        self.active.add(key)
        if ref in self.records:
            r = self.records[ref]
            need(r["status"] == "confirmed" and r["evidence_class"] not in {"secondary_lead", "unverified_lead"}, f"{ref}: unverified/conflicted evidence cannot support valuation")
            need(numeric(r["value"]), f"{ref}: quantitative support needs numeric value")
            need(not forward or r["source_kind"] == "fundamental", f"{ref}: market information contaminates forward value")
            result = (r["value"], r["unit"], r["business_line"], r["driver"], {ref})
            if forward:
                self.forward_refs.add(ref)
        else:
            need(ref in self.nodes, f"unresolved provenance: {ref}")
            n = self.nodes[ref]
            need(isinstance(n, dict), f"{ref}: node must be an object")
            for field in ("unit", "business_line", "driver", "rationale"):
                need(nonempty(n.get(field)), f"{ref}: {field} required")
            need(instant(n.get("available_at")) <= self.cutoff, f"{ref}: node available after cutoff")
            refs = n.get("evidence_refs")
            need(isinstance(refs, list) and refs and len(set(refs)) == len(refs), f"{ref}: unique evidence_refs required")
            dependencies = [self.resolve(r, forward) for r in refs]
            records = set().union(*(d[4] for d in dependencies))
            kind = n.get("kind")
            if kind == "assumption":
                value = n.get("value")
                bounds = n.get("bounds")
                need(isinstance(bounds, list) and len(bounds) == 2 and all(numeric(x) for x in bounds) and numeric(value) and bounds[0] <= value <= bounds[1], f"{ref}: assumption needs explicit finite bounds containing its value")
                need(nonempty(n.get("bounds_basis")), f"{ref}: bounds_basis required")
                need(n.get("bounded_by_evidence") in (True, False), f"{ref}: bounded_by_evidence required")
                if n["bounded_by_evidence"] is not True:
                    need(self.p["analysis_mode"] == "conditional", f"{ref}: evidence cannot bound assumption; only conditional analysis allowed")
                    self.conditional.add(ref)
                self.assumptions.add(ref)
            elif kind == "calculation":
                args = n.get("args")
                need(isinstance(args, list) and args and all(nonempty(a) for a in args), f"{ref}: calculation args must be reference IDs; no anonymous constants")
                need(set(args) == set(refs), f"{ref}: every formula operand must be in evidence_refs")
                resolved = [self.resolve(a, forward) for a in args]
                numbers = [d[0] for d in resolved]
                op = n.get("op")
                if op in {"add", "subtract", "min", "max"}:
                    need(all(d[1] == n["unit"] for d in resolved), f"{ref}: incompatible additive units")
                if op == "identity":
                    need(len(numbers) == 1 and resolved[0][1] == n["unit"], f"{ref}: invalid identity")
                    value = numbers[0]
                elif op == "add": value = sum(numbers)
                elif op == "subtract":
                    need(len(numbers) == 2, f"{ref}: subtract needs two args")
                    value = numbers[0] - numbers[1]
                elif op == "multiply": value = math.prod(numbers)
                elif op == "divide":
                    need(len(numbers) == 2 and numbers[1] != 0, f"{ref}: invalid division")
                    value = numbers[0] / numbers[1]
                elif op == "min": value = min(numbers)
                elif op == "max": value = max(numbers)
                else: raise ContractError(f"{ref}: unsupported formula operation")
                need(nonempty(n.get("unit_derivation")), f"{ref}: unit_derivation required")
                # Dangerous operational stages require an explicit adjustment,
                # not an identity that relabels commitments as realized output.
                dangerous = {"framework_order", "channel_shipment", "planned_capacity"}
                target = n["driver"]
                if target in {"quantity", "revenue", "cash_flow", "terminal_demand", "effective_capacity"} and any(self.records[r]["supply_chain_stage"] in dangerous for r in records):
                    need(op not in {"identity", "add"} and nonempty(n.get("conversion_basis")) and len(records) >= 2, f"{ref}: stage conversion lacks evidence-backed adjustment")
            else:
                raise ContractError(f"{ref}: node kind must be assumption or calculation")
            need(numeric(value), f"{ref}: non-finite calculation")
            result = (value, n["unit"], n["business_line"], n["driver"], records)
        self.active.remove(key)
        self.cache[key] = result
        return result

    def bind(self, inputs, refs, business, forward=True):
        need(isinstance(refs, dict), "leaf provenance must be an object")
        values = dict(leaves(inputs))
        need(set(refs) == set(values), f"{business}: provenance must cover exactly every numeric leaf (including nested arrays)")
        for path, value in values.items():
            computed, unit, line, driver, records = self.resolve(refs[path], forward)
            need(math.isclose(value, computed, rel_tol=1e-10, abs_tol=1e-10), f"{path}: value disagrees with resolved provenance")
            need(unit == unit_for(path, self.p["currency"], self.p["amount_unit"]), f"{path}: unit/currency/scale mismatch")
            need(line == business and driver == driver_for(path), f"{path}: reference does not support this business/driver")
            if forward and driver in {"cash_flow", "quantity", "revenue", "terminal_demand", "effective_capacity"} and refs[path] in self.records:
                need(self.records[refs[path]]["supply_chain_stage"] not in {"framework_order", "channel_shipment", "planned_capacity"}, f"{path}: unconverted operational stage")

    def gate(self):
        p = self.p
        plan = p.get("research_plan")
        need(isinstance(plan, dict), "independent research_plan required")
        need(instant(plan.get("defined_at")) <= self.cutoff and nonempty(plan.get("materiality_basis")), "dated materiality design required")
        threshold = plan.get("materiality_threshold")
        need(numeric(threshold) and 0 <= threshold <= 1, "materiality_threshold must be explicit")
        business = plan.get("businesses")
        need(isinstance(business, list) and business, "complete business inventory required")
        names = [b["name"] for b in business]
        need(len(names) == len(set(names)), "duplicate business")
        weights = [b["weight"] for b in business]
        need(all(numeric(w) and 0 <= w <= 1 for w in weights) and math.isclose(sum(weights), 1), "business weights must cover entire perimeter and sum to one")
        scopes = []
        for b in business:
            need(nonempty(b.get("weight_basis")) and nonempty(b.get("routing_basis")), "business weights/routing need rationale")
            need(isinstance(b.get("economic_ids"), list) and b["economic_ids"] and all(nonempty(x) for x in b["economic_ids"]), "economic_ids must identify underlying businesses/assets")
            scopes += b["economic_ids"]
            need(b.get("industry") in ROUTES and b.get("method") in ROUTES[b["industry"]], f"{b['name']}: method gap for requested industry; no fallback")
            need(set(b.get("drivers", [])) >= DRIVERS[b["method"]], f"{b['name']}: required operating/model drivers omitted")
        need(len(scopes) == len(set(scopes)), "overlapping economic interests would be double counted")
        gate = p.get("evidence_gate")
        need(isinstance(gate, dict) and instant(gate.get("as_of")) == self.cutoff, "gate cutoff mismatch")
        need(gate.get("status") == "pass" and gate.get("critical_missing") == [] and gate.get("material_conflicts") == [], "gate has gaps/conflicts")
        drivers = gate.get("drivers")
        need(isinstance(drivers, list), "gate drivers required")
        pairs = [(d["business_line"], d["name"]) for d in drivers]
        need(len(pairs) == len(set(pairs)), "duplicate gate driver")
        expected = {(b["name"], d) for b in business if b["weight"] >= threshold or b.get("material_override") is True for d in b["drivers"]}
        need(expected <= set(pairs), "material business/driver missing from gate")
        known = {(b["name"], d) for b in business for d in b["drivers"]}
        need(set(pairs) <= known, "gate driver not in research plan")
        rules = plan.get("rules")
        need(isinstance(rules, dict), "numeric sufficiency rules required")
        for d in drivers:
            pair = (d["business_line"], d["name"])
            if pair not in expected:
                continue
            rule = rules.get(f"{pair[0]}/{pair[1]}")
            need(isinstance(rule, dict) and nonempty(rule.get("rationale")), f"{pair}: explicit thresholds and rationale required")
            for field in ("min_independent", "min_primary"):
                x = rule.get(field)
                need(type(x) is int and x >= 0, f"{pair}: invalid {field}")
            need(rule["min_independent"] >= 1, "material driver requires at least one identifiable original source")
            need(numeric(rule.get("max_age_hours")) and rule["max_age_hours"] >= 0, "freshness threshold required")
            need(numeric(rule.get("min_coverage")) and 0 <= rule["min_coverage"] <= 1, "coverage threshold required")
            refs = d.get("record_ids")
            need(isinstance(refs, list) and refs and len(refs) == len(set(refs)), "driver needs unique ledger record IDs")
            need(all(r in self.records for r in refs), "gate references nonexistent record")
            records = [self.records[r] for r in refs]
            need(all(r["business_line"] == pair[0] for r in records), "evidence belongs to another business")
            for r in refs:
                self.resolve(r)
            need(all(r["scope"] == d.get("scope") for r in records), "evidence scope mismatch")
            groups = {r["source_group"] for r in records}
            primary = {r["source_group"] for r in records if r["evidence_class"] == "primary_confirmation"}
            need(len(groups) >= rule["min_independent"] and len(primary) >= rule["min_primary"], "independence/primary thresholds fail")
            need(all(r["coverage"] >= rule["min_coverage"] for r in records), "coverage threshold fails")
            need(all(r["observed_at"] is not None and 0 <= (self.cutoff - instant(r["observed_at"])).total_seconds() / 3600 <= rule["max_age_hours"] for r in records), "stale/future observation")
            bound_refs = d.get("bounds_refs")
            need(isinstance(bound_refs, list) and len(bound_refs) == 2, "driver needs resolvable interval bounds")
            low, high = [self.resolve(r) for r in bound_refs]
            need(low[0] <= high[0] and low[1:4] == high[1:4] and low[2:4] == pair, "invalid/mismapped interval bounds")
            need((low[4] | high[4]) <= set(refs), "bounds not supported by declared driver records")
            causal_ref = d.get("causal_ref")
            causal = self.resolve(causal_ref)
            need(causal[2:4] == pair and causal[1] == low[1] and low[0] <= causal[0] <= high[0], "causal input outside supported interval")
            need(causal[4] <= set(refs), "causal chain not supported by gate evidence")
            conflicts = {r["record_id"] for r in self.records.values() if r["business_line"] == pair[0] and r["driver"] == pair[1] and r["status"] in {"conflicted", "missing"}}
            need(not conflicts, "ledger includes unresolved material conflict/missing data")
            self.coverage.append({"business": pair[0], "driver": pair[1], "independent_sources": len(groups), "primary_sources": len(primary), "coverage_floor": min(r["coverage"] for r in records), "interval": [low[0], high[0]]})
        self.businesses = {b["name"]: b for b in business}
        self.gate_drivers = {pair: d for pair, d in zip(pairs, drivers)}

    def scenario(self, s):
        segments = s["segments"]
        need(len({x["name"] for x in segments}) == len(segments), "duplicate segment")
        need({x["name"] for x in segments} == set(self.businesses), "scenario must cover full business inventory")
        for seg in segments:
            b = self.businesses[seg["name"]]
            need(seg["method"] == b["method"], "scenario changed approved industry route")
            self.bind(seg["inputs"], seg["provenance"], seg["name"])
            for path, value in leaves(seg["inputs"]):
                d = self.gate_drivers.get((seg["name"], driver_for(path)))
                if d:
                    lo, hi = [self.resolve(r)[0] for r in d["bounds_refs"]]
                    need(lo <= value <= hi, f"{path}: scenario input outside gate interval")
        self.bind({"probability": s["probability"]}, {"probability": s.get("probability_ref")}, "__group__")
        self.bind(s["equity_bridge"], s["bridge_provenance"], "__group__")
        allocation = s.get("bridge_allocations")
        need(isinstance(allocation, dict) and set(allocation) == set(s["equity_bridge"]) - {"diluted_shares"}, "bridge_allocations must cover every adjustment")
        identifiers = {x for b in self.businesses.values() for x in b["economic_ids"]}
        for category, items in allocation.items():
            need(isinstance(items, list), "bridge allocation must be a list; explicit empty list means proven zero")
            total = 0
            for item in items:
                need(isinstance(item, dict) and nonempty(item.get("id")) and item["id"] not in identifiers, "duplicate economic asset/claim in bridge")
                identifiers.add(item["id"])
                owner = item.get("owner")
                need(owner == "__parent__" or owner in self.businesses, "bridge owner must be parent or identified business")
                if owner != "__parent__":
                    target = next(x for x in segments if x["name"] == owner)
                    need(target["basis"] == "enterprise", "direct equity segment already includes its own cash/debt/minority claims")
                if category == "minority_interest":
                    need(owner != "__parent__", "minority claim must identify the consolidated enterprise segment")
                value, unit, _, _, _ = self.resolve(item.get("ref"))
                need(unit == f"{self.p['currency']}:{self.p['amount_unit']}" and value >= 0, "bridge adjustment unit/sign mismatch")
                total += value
            need(math.isclose(total, s["equity_bridge"][category], abs_tol=1e-10), "bridge allocations do not reconcile to adjustment")
        need(all(x >= 0 for x in s["equity_bridge"].values()), "bridge uses nonnegative amounts and separately defined signs")

    def run(self):
        self.gate()
        need(isinstance(self.p.get("scenarios"), list) and self.p["scenarios"], "scenarios required")
        need(len({s["name"] for s in self.p["scenarios"]}) == len(self.p["scenarios"]), "duplicate scenario")
        for s in self.p["scenarios"]:
            self.scenario(s)
        return {"computed_status": "conditional" if self.conditional else "pass", "coverage": self.coverage, "assumptions": sorted(self.assumptions), "unbounded_conditions": sorted(self.conditional)}


def audit(payload):
    try:
        checker = Audit(payload)
        report = checker.run()
        return checker, report
    except (KeyError, TypeError, OverflowError, RecursionError) as exc:
        raise ContractError(f"malformed/unsupported evidence contract: {exc}") from exc

