#!/usr/bin/env python3
"""Measure Codex skill discovery and conditional-entry context in characters.

Character counts are reproducible across machines. They are not presented as
token counts because Chinese and structured text tokenize differently by model.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
FIELD_RE = re.compile(r"(?m)^(name|description):\s*[\"']?(.*?)[\"']?\s*$")


def inspect_skill(folder: Path) -> Dict[str, Any]:
    entry = folder / "SKILL.md"
    text = entry.read_text(encoding="utf-8-sig")
    match = FRONTMATTER_RE.search(text)
    fields: Dict[str, str] = {}
    if match:
        for key, value in FIELD_RE.findall(match.group(1)):
            fields[key] = value.strip().strip('"').strip("'")
    policy = folder / "agents" / "openai.yaml"
    explicit_only = policy.is_file() and bool(
        re.search(r"(?m)^\s*allow_implicit_invocation:\s*false\s*$", policy.read_text(encoding="utf-8-sig"))
    )
    name = fields.get("name", folder.name)
    description = fields.get("description", "")
    return {
        "name": name,
        "path": str(entry.relative_to(folder.parent)),
        "explicit_only": explicit_only,
        "description_chars": len(description),
        "entry_chars": len(text),
        "discovery_chars_estimate": len(name) + len(description) + len(str(entry.relative_to(folder.parent))),
    }


def audit(root: Path) -> Dict[str, Any]:
    skills = [inspect_skill(path) for path in sorted(root.iterdir()) if path.is_dir() and (path / "SKILL.md").is_file()]
    implicit = [item for item in skills if not item["explicit_only"]]
    return {
        "root": str(root),
        "skill_count": len(skills),
        "explicit_only_count": len(skills) - len(implicit),
        "description_chars_all": sum(item["description_chars"] for item in skills),
        "description_chars_implicit": sum(item["description_chars"] for item in implicit),
        "discovery_chars_estimate_implicit": sum(item["discovery_chars_estimate"] for item in implicit),
        "entry_chars_conditional": sum(item["entry_chars"] for item in skills),
        "skills": skills,
    }


def apply_budget(report: Dict[str, Any], config: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    maximum = config.get("max_implicit_description_chars")
    if isinstance(maximum, int) and report["description_chars_implicit"] > maximum:
        errors.append(
            f"implicit description characters {report['description_chars_implicit']} exceed budget {maximum}"
        )
    per_skill = config.get("max_single_description_chars")
    if isinstance(per_skill, int):
        for item in report["skills"]:
            if item["description_chars"] > per_skill:
                errors.append(
                    f"{item['name']} description has {item['description_chars']} characters; budget is {per_skill}"
                )
    return errors


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit skill context in stable character counts.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "evals" / "context-budget" / "budget.json")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    report = audit(args.root.resolve())
    config = json.loads(args.config.read_text(encoding="utf-8")) if args.config.is_file() else {}
    errors = apply_budget(report, config)
    report["budget"] = config
    report["errors"] = errors
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"skills: {report['skill_count']} ({report['explicit_only_count']} explicit-only)")
        print(f"description chars, all: {report['description_chars_all']}")
        print(f"description chars, implicit: {report['description_chars_implicit']}")
        print(f"discovery chars estimate, implicit: {report['discovery_chars_estimate_implicit']}")
        print(f"SKILL.md chars, conditional: {report['entry_chars_conditional']}")
        print("budget: " + ("PASS" if not errors else "FAIL"))
        for error in errors:
            print(f"- {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
