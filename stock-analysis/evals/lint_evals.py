#!/usr/bin/env python3
"""Lint stock-analysis behavioral eval metadata and fixture references."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent


def lint() -> list[str]:
    errors: list[str] = []
    data = json.loads((HERE / "evals.json").read_text(encoding="utf-8"))
    cases = data.get("evals")
    if not isinstance(cases, list) or not cases:
        return ["evals must be a non-empty list"]
    ids = set()
    names = set()
    for index, case in enumerate(cases):
        label = case.get("name", f"index-{index}")
        for key in ("id", "name", "prompt", "expected_output", "files", "assertions"):
            if key not in case:
                errors.append(f"{label}: missing {key}")
        if case.get("id") in ids:
            errors.append(f"duplicate id: {case.get('id')}")
        ids.add(case.get("id"))
        if label in names:
            errors.append(f"duplicate name: {label}")
        names.add(label)
        assertions = case.get("assertions")
        if not isinstance(assertions, list) or len(assertions) < 3:
            errors.append(f"{label}: requires at least three behavioral assertions")
        for relative in case.get("files", []):
            if not (HERE / relative).is_file():
                errors.append(f"{label}: missing fixture {relative}")
    required = {
        "a-share-disclosure-routing", "a-share-ttm-and-ma-commitment",
        "leading-signals-before-financials", "freshness-is-not-reliability",
        "financial-reconciliation-conflict-loop",
    }
    missing = required - names
    if missing:
        errors.append(f"missing A-share regression cases: {', '.join(sorted(missing))}")
    return errors


def main() -> int:
    errors = lint()
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: stock-analysis eval metadata and fixtures are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
