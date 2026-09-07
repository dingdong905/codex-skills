#!/usr/bin/env python3
"""校验 PPT Skills 结构，并对路由/文本预测做基础评分。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CASES = HERE / "cases.json"
SPECIALISTS = {
    "technical-explainer-deck",
    "executive-decision-deck",
    "research-presentation",
    "pitch-deck",
    "data-report-deck",
    "teaching-deck",
    "deck-review",
}
REQUIRED_FILES = [
    "presentation-studio/SKILL.md",
    "presentation-studio/references/contracts.md",
    "technical-explainer-deck/SKILL.md",
    "technical-explainer-deck/references/story-and-pages.md",
    "executive-decision-deck/SKILL.md",
    "research-presentation/SKILL.md",
    "pitch-deck/SKILL.md",
    "data-report-deck/SKILL.md",
    "teaching-deck/SKILL.md",
    "deck-review/SKILL.md",
    "deck-review/references/rubric.md",
    "deck-review/scripts/deck_audit.py",
]
CHAR_LIMITS = {
    "presentation-studio/SKILL.md": 5500,
    "technical-explainer-deck/SKILL.md": 9000,
    "executive-decision-deck/SKILL.md": 4000,
    "research-presentation/SKILL.md": 4000,
    "pitch-deck/SKILL.md": 4000,
    "data-report-deck/SKILL.md": 4000,
    "teaching-deck/SKILL.md": 4000,
    "deck-review/SKILL.md": 5500,
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def lint() -> int:
    errors = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"缺少文件: {relative}")
    for relative, limit in CHAR_LIMITS.items():
        path = ROOT / relative
        if path.is_file() and len(path.read_text(encoding="utf-8")) > limit:
            errors.append(f"入口过长: {relative} > {limit}")
    payload = load(CASES)
    cases = payload.get("cases", [])
    ids = [case.get("id") for case in cases]
    if len(ids) != len(set(ids)):
        errors.append("评测 case id 重复")
    covered = {case.get("expected_skill") for case in cases}
    missing = sorted(SPECIALISTS - covered)
    if missing:
        errors.append(f"缺少品类路由用例: {', '.join(missing)}")
    if not any(case.get("kind") == "safety" for case in cases):
        errors.append("缺少硬失败用例")
    for case in cases:
        if not case.get("prompt") or not case.get("expected_skill"):
            errors.append(f"字段不完整: {case.get('id')}")
    print(json.dumps({"ok": not errors, "cases": len(cases), "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


def score(predictions_path: Path) -> int:
    cases = {case["id"]: case for case in load(CASES)["cases"]}
    predictions = load(predictions_path)
    results = []
    for prediction in predictions:
        case = cases[prediction["id"]]
        response = str(prediction.get("response", ""))
        route = 30 if prediction.get("selected_skill") == case["expected_skill"] else 0
        concepts = case.get("required_concepts", [])
        lowered = response.casefold()
        matched = sum(any(term.casefold() in lowered for term in group) for group in concepts)
        quality = 50 if not concepts else round(50 * matched / len(concepts), 2)
        budget = 20 if len(response) <= int(case.get("max_response_chars", 999999)) else 0
        total = round(route + quality + budget, 2)
        results.append({"id": case["id"], "score": total, "passed": total >= 80, "route_exact": route == 30, "concepts": f"{matched}/{len(concepts)}", "within_budget": budget == 20})
    complete = len(results) == len(cases)
    passed = complete and all(item["passed"] for item in results)
    print(json.dumps({"passed": passed, "coverage": f"{len(results)}/{len(cases)}", "results": results, "note": "仍需按 rubric.md 审阅真实 PPTX。"}, ensure_ascii=False, indent=2))
    return 0 if passed else 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("lint")
    scorer = commands.add_parser("score")
    scorer.add_argument("predictions", type=Path)
    args = parser.parse_args(argv)
    try:
        return lint() if args.command == "lint" else score(args.predictions)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"score_eval: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

