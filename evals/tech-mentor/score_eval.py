#!/usr/bin/env python3
"""Static lint for tech-mentor regression cases and explicit-only policy."""

from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def lint() -> list[str]:
    errors: list[str] = []
    data = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["cases must be a non-empty list"]
    ids: set[str] = set()
    for index, case in enumerate(cases):
        label = case.get("id", f"index-{index}")
        if label in ids:
            errors.append(f"duplicate case id: {label}")
        ids.add(label)
        for key in ("id", "kind", "prompt", "should_invoke", "expected_mode", "required_concepts", "max_response_chars"):
            if key not in case:
                errors.append(f"{label}: missing {key}")
        if not isinstance(case.get("max_response_chars"), int) or case.get("max_response_chars", 0) <= 0:
            errors.append(f"{label}: max_response_chars must be positive")
    if not any(case.get("should_invoke") is False for case in cases):
        errors.append("at least one negative routing case is required")
    policy = (ROOT / "tech-mentor" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "allow_implicit_invocation: false" not in policy:
        errors.append("tech-mentor must remain explicit-only")
    return errors


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] != "lint":
        print("usage: python evals/tech-mentor/score_eval.py lint", file=sys.stderr)
        return 2
    errors = lint()
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: tech-mentor eval cases and explicit-only policy are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
