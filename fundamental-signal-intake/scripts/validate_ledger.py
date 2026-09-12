#!/usr/bin/env python3
"""Validate a point-in-time fundamental evidence ledger.

Standard-library only. Fails closed: missing fields, invalid dates, duplicate IDs,
or look-ahead leakage produce a non-zero exit code.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
import math
from pathlib import Path


REQUIRED = {
    "record_id",
    "entity",
    "business_line",
    "supply_chain_stage",
    "metric",
    "value",
    "unit",
    "geography",
    "product_or_project",
    "counterparty",
    "observed_at",
    "published_at",
    "collected_at",
    "source_title",
    "source_publisher",
    "source_url_or_file",
    "source_excerpt",
    "evidence_class",
    "confidence",
    "cross_checks",
    "status",
    "notes",
    "driver", "source_group", "available_at", "vintage_at", "vintage_id",
    "snapshot_reference", "coverage", "scope", "source_kind",
}
EVIDENCE_CLASSES = {
    "physical_flow",
    "price_order_inventory",
    "primary_confirmation",
    "secondary_lead",
    "unverified_lead",
}
CONFIDENCE = {"high", "medium", "low"}
STATUS = {
    "confirmed",
    "calculated",
    "source_claim",
    "unverified",
    "conflicted",
    "missing",
}


def parse_day(
    value: object,
    field: str,
    errors: list[str],
    record_id: str,
    *,
    allow_null: bool = False,
) -> datetime | None:
    if value is None and allow_null:
        return None
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{record_id}: {field} must be a non-empty ISO date/time")
        return None
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError("timezone required")
        return result.astimezone(timezone.utc)
    except ValueError:
        errors.append(f"{record_id}: invalid {field}: timezone-aware ISO timestamp required")
        return None


def validate(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["ledger must be a JSON object"]
    as_of = parse_day(payload.get("as_of"), "as_of", errors, "ledger")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        errors.append("ledger.records must be a non-empty list")
        return errors

    seen: set[str] = set()
    all_ids = {r.get("record_id") for r in records if isinstance(r, dict) and isinstance(r.get("record_id"), str)}
    for index, record in enumerate(records):
        rid = f"record[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{rid}: must be an object")
            continue
        missing = sorted(REQUIRED - record.keys())
        if missing:
            errors.append(f"{rid}: missing fields: {', '.join(missing)}")
        record_id = str(record.get("record_id") or rid)
        if record_id in seen:
            errors.append(f"{record_id}: duplicate record_id")
        seen.add(record_id)

        published = parse_day(record.get("published_at"), "published_at", errors, record_id)
        observed = parse_day(
            record.get("observed_at"),
            "observed_at",
            errors,
            record_id,
            allow_null=record.get("status") in {"source_claim", "unverified", "conflicted", "missing"},
        )
        collected = parse_day(record.get("collected_at"), "collected_at", errors, record_id)
        available = parse_day(record.get("available_at"), "available_at", errors, record_id)
        vintage = parse_day(record.get("vintage_at"), "vintage_at", errors, record_id)
        if as_of and available and available > as_of:
            errors.append(f"{record_id}: look-ahead leak; available_at is after as_of")
        if published and vintage and available and collected:
            if not published <= vintage <= available <= collected:
                errors.append(f"{record_id}: require published_at <= vintage_at <= available_at <= collected_at")
        if record.get("source_kind") not in {"fundamental", "market"}:
            errors.append(f"{record_id}: invalid source_kind")
        coverage = record.get("coverage")
        if isinstance(coverage, bool) or not isinstance(coverage, (int, float)) or not math.isfinite(coverage) or not 0 <= coverage <= 1:
            errors.append(f"{record_id}: coverage must be a finite fraction in [0,1]")
        if isinstance(record.get("value"), (int, float)) and (isinstance(record["value"], bool) or not math.isfinite(record["value"])):
            errors.append(f"{record_id}: value must be finite and not boolean")
        if as_of and published and published > as_of:
            errors.append(f"{record_id}: look-ahead leak; published_at {published} is after as_of {as_of}")
        if as_of and observed and observed > as_of and record.get("status") == "confirmed":
            errors.append(f"{record_id}: future observed_at cannot be confirmed as of {as_of}")

        if record.get("evidence_class") not in EVIDENCE_CLASSES:
            errors.append(f"{record_id}: invalid evidence_class")
        if record.get("confidence") not in CONFIDENCE:
            errors.append(f"{record_id}: invalid confidence")
        if record.get("status") not in STATUS:
            errors.append(f"{record_id}: invalid status")
        if record.get("status") != "missing" and record.get("value") is None:
            errors.append(f"{record_id}: value cannot be null unless status is missing")
        if "cross_checks" in record and not isinstance(record["cross_checks"], list):
            errors.append(f"{record_id}: cross_checks must be a list")
        elif isinstance(record.get("cross_checks"), list):
            for ref in record["cross_checks"]:
                if not isinstance(ref, str) or ref not in all_ids or ref == record_id:
                    errors.append(f"{record_id}: cross_checks contains an unresolved or self reference")
        if record.get("status") == "calculated":
            errors.append(f"{record_id}: calculated records must use the valuation derivation graph, not unverified ledger values")
        for field in (
            "entity",
            "business_line",
            "supply_chain_stage",
            "metric",
            "unit",
            "source_title",
            "source_publisher",
            "source_url_or_file",
            "source_excerpt",
            "notes",
            "record_id", "driver", "source_group", "vintage_id", "snapshot_reference", "scope",
        ):
            if field in record and (not isinstance(record[field], str) or not record[field].strip()):
                errors.append(f"{record_id}: {field} must be non-empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.ledger.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    errors = validate(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"valid ledger: {len(payload['records'])} records, as_of={payload['as_of']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

