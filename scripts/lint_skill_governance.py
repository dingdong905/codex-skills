#!/usr/bin/env python3
"""Validate skill layout; semantic generality and evidence require separate review."""
import argparse
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import unquote

EXAMPLE_HEADING = re.compile(r"(?i)(\b(?:worked |usage |visual |button |color palette )?examples?\b|(?:边界)?案例|示例|实例复盘)")
PERSONAL_PATH = re.compile(r"[A-Za-z]:\\{1,2}(?:Users\\{1,2}[^<{\s\\\x60]+|python(?:\\|/)|msys2(?:\\|/)|skills(?:\\|/))")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\n]+)\)")
SKIP = {"__pycache__", ".git", ".venv"}

def prose(text):
    fence = None
    for n, line in enumerate(text.splitlines(), 1):
        m = re.match(r"^\s*(\x60{3,}|~{3,})", line)
        if m:
            mark = m.group(1)
            if fence is None:
                fence = (mark[0], len(mark))
            elif mark[0] == fence[0] and len(mark) >= fence[1]:
                fence = None
            continue
        if fence is None:
            yield n, line

def contained(path, root):
    return path.resolve().is_relative_to(root.resolve())

def audit(root, selected=None):
    errors = []
    skills = sorted(p.parent for p in root.glob("*/SKILL.md") if not selected or p.parent.name in selected)
    if selected:
        for name in sorted(set(selected) - {p.name for p in skills}):
            errors.append(f"{name}: skill not found")
    def error(path, msg, line=None):
        label = path.relative_to(root).as_posix()
        errors.append(f"{label}{':' + str(line) if line else ''}: {msg}")
    for skill in skills:
        entry = skill / "SKILL.md"
        text = entry.read_text(encoding="utf-8-sig")
        fm = re.match(r"\A---\s*\n(.*?)\n---(?:\s*\n|$)", text, re.S)
        if not fm:
            error(entry, "missing frontmatter")
        else:
            for field in ("name", "description"):
                match = re.search(rf"(?m)^{field}:\s*(.+)$", fm.group(1))
                if not match:
                    error(entry, f"missing {field}")
                elif field == "name" and match.group(1).strip().strip("'\"") != skill.name:
                    error(entry, "name must match skill directory")
        for path in skill.rglob("*"):
            rel = path.relative_to(skill)
            if any(x in SKIP for x in rel.parts):
                continue
            if path.is_dir() and path.name in {"examples", "samples"}:
                error(path, "use singular example/ for concrete cases")
            if path.is_file() and (rel.parts[:2] == ("references", "topics") or (rel.parts[0] == "assets" and re.match(r"(?i)(?:sample|example|demo)[_-]", path.name))):
                error(path, "concrete topic/sample belongs in example/")
            if not path.is_file() or path.suffix != ".md" or rel.parts[0] in {"example", "tests", "evals"} or path.name == "SKILL.en.md":
                continue
            content = path.read_text(encoding="utf-8-sig")
            if path == entry or rel.parts[0] == "references":
                for n, line in enumerate(content.splitlines(), 1):
                    if PERSONAL_PATH.search(line):
                        error(path, "machine-specific absolute path belongs in example/ or workspace context", n)
                lines = list(prose(content))
                for idx, (n, line) in enumerate(lines):
                    heading = re.match(r"^(#{1,6})\s+(.+)", line)
                    if not heading or not EXAMPLE_HEADING.search(heading.group(2)):
                        continue
                    body = []
                    # Include fenced examples; only real headings delimit sections.
                    next_boundary = next((ln for ln, s in lines[idx + 1:] if re.match(r"^#{1," + str(len(heading.group(1))) + r"}\s+", s)), len(content.splitlines()) + 1)
                    for next_line in content.splitlines()[n:next_boundary - 1]:
                        h = re.match(r"^(#{1,6})\s+", next_line)
                        if h and len(h.group(1)) <= len(heading.group(1)):
                            break
                        if next_line.strip() and next_line.strip() != "---":
                            body.append(next_line)
                    if body and not all(re.search(r"(?:\.\./)?example/", s) for s in body):
                        error(path, "move example content to example/; retain conditional links only", n)
            for n, line in prose(content):
                for match in LINK.finditer(line):
                    target = match.group(1).strip()
                    target = target.split(">")[0][1:] if target.startswith("<") else target.split(' "')[0]
                    if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith(("#", "/")):
                        continue
                    target = unquote(target.split("#")[0].split("?")[0])
                    if not target or any(c in target for c in "<>{}*"):
                        continue
                    resolved = path.parent / target
                    if not contained(resolved, skill):
                        error(path, f"local resource leaves installable skill: {target}", n)
                    elif not resolved.exists():
                        error(path, f"broken local link: {target}", n)
        example = skill / "example"
        if not example.is_dir():
            continue
        files = {p.relative_to(example).as_posix() for p in example.rglob("*") if p.is_file() and not any(x in SKIP for x in p.relative_to(example).parts) and p.name != "index.json"}
        if not files:
            error(example, "do not create empty example directories")
            continue
        index = example / "index.json"
        if not index.is_file():
            error(example, "example/index.json is required")
            continue
        try:
            manifest = json.loads(index.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError) as exc:
            error(index, f"invalid JSON: {exc}")
            continue
        if not isinstance(manifest, dict) or manifest.get("version") != 1 or not isinstance(manifest.get("cases"), list) or not manifest["cases"]:
            error(index, "expected version=1 and nonempty cases array")
            continue
        declared, ids = set(), set()
        for case in manifest["cases"]:
            if not isinstance(case, dict):
                error(index, "case must be an object")
                continue
            for key in ("id", "kind", "scenario", "preconditions", "expected", "limits", "source"):
                if not isinstance(case.get(key), str) or not case[key].strip():
                    error(index, f"case {case.get('id', '?')} needs nonempty {key}")
            case_id = case.get("id", "")
            if not isinstance(case_id, str):
                case_id = ""
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", case_id) or case_id in ids:
                error(index, f"invalid or duplicate id: {case_id}")
            ids.add(case_id)
            if case.get("kind") not in {"observed", "synthetic", "teaching"}:
                error(index, f"{case_id}: invalid kind")
            try:
                date.fromisoformat(case.get("verified_at", ""))
            except (ValueError, TypeError):
                if case.get("verified_at") != "unknown":
                    error(index, f"{case_id}: verified_at must be ISO date or unknown")
            case_files = case.get("files")
            if not isinstance(case_files, list) or not case_files:
                error(index, f"{case_id}: files must be a nonempty array")
                continue
            for name in case_files:
                if not isinstance(name, str) or "\\" in name or not contained(example / name, example):
                    error(index, f"{case_id}: invalid file path {name}")
                    continue
                if name in declared:
                    error(index, f"file declared twice: {name}")
                declared.add(name)
                if name not in files:
                    error(index, f"missing example file: {name}")
        for name in sorted(files - declared):
            error(index, f"unregistered example file: {name}")
    return {"root": str(root), "skills": len(skills), "errors": errors}

def fingerprint(root, message):
    import hashlib
    relative = message.split(": ", 1)[0]
    relative = re.sub(r":\d+$", "", relative)
    path = root / relative
    digest = hashlib.sha256()
    if path.is_file():
        digest.update(path.read_bytes())
    elif path.is_dir():
        for child in sorted(p for p in path.rglob("*") if p.is_file() and not any(x in SKIP for x in p.relative_to(path).parts)):
            digest.update(child.relative_to(path).as_posix().encode())
            digest.update(child.read_bytes())
    return digest.hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skill", action="append", help="Check a touched skill without legacy exceptions")
    parser.add_argument("--baseline", type=Path, help="Allow only unchanged legacy violations")
    args = parser.parse_args()
    root = args.root.resolve()
    report = audit(root, args.skill)
    if args.baseline and args.skill:
        parser.error("--baseline must not be used with --skill")
    if args.baseline:
        baseline = json.loads(args.baseline.read_text(encoding="utf-8-sig"))
        known = {(x["error"], x["sha256"]) for x in baseline["violations"]}
        current = report["errors"]
        report["errors"] = [msg for msg in current if (msg, fingerprint(root, msg)) not in known]
        report["legacy_violations"] = len(current) - len(report["errors"])
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Skill governance: {report['skills']} skills; {len(report['errors'])} errors")
        if report.get("legacy_violations"):
            print(f"Unchanged legacy violations awaiting approved migration: {report['legacy_violations']}")
        for msg in report["errors"]:
            print("- " + msg)
        print("Semantic generality and evidence still require review.")
    return 1 if report["errors"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
