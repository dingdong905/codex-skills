#!/usr/bin/env python3
"""Local handoff state capture and comparison; no network or conversation export."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

REQUIRED = ("目标与验收", "工作区", "当前状态与证据", "决策与边界",
            "关键产物与读取顺序", "剩余工作与阻塞", "下一步", "粘贴首句")

def digest(data):
    return hashlib.sha256(data).hexdigest()

def selected_file(workspace, name):
    relative = Path(name)
    if relative.is_absolute() or not name.strip():
        raise ValueError("selected file must be a nonempty relative path")
    target = (workspace / relative).resolve()
    if not target.is_relative_to(workspace):
        raise ValueError("selected file escapes workspace")
    if not target.is_file():
        raise ValueError("selected file missing or not a regular file: " + name)
    return target, relative.as_posix()

def git_state(workspace):
    executable = shutil.which("git")
    if not executable:
        return None, ["git-unavailable"]
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    def run(*args, optional=False):
        p = subprocess.run([executable, "-C", str(workspace), *args],
                           capture_output=True, env=env, timeout=30)
        if p.returncode:
            if optional:
                return None
            raise ValueError("git state collection failed: " + args[0])
        return p.stdout
    root_bytes = run("rev-parse", "--show-toplevel", optional=True)
    if root_bytes is None:
        for directory in (workspace, *workspace.parents):
            if (directory / ".git").exists():
                raise ValueError("Git metadata exists but repository cannot be read")
        return None, ["not-a-git-worktree"]
    root = Path(root_bytes.decode("utf-8", errors="surrogateescape").strip()).resolve()
    head = run("rev-parse", "--verify", "HEAD", optional=True)
    branch = run("symbolic-ref", "--quiet", "--short", "HEAD", optional=True)
    status = run("status", "--porcelain=v1", "-z", "--untracked-files=all")
    return {
        "root": str(root),
        "workspace_from_root": workspace.relative_to(root).as_posix(),
        "head": head.decode("ascii").strip() if head else None,
        "branch": branch.decode("utf-8", errors="surrogateescape").strip() if branch else None,
        "status": status.decode("utf-8", errors="surrogateescape").split("\0")[:-1],
        "staged_diff_sha256": digest(run("diff", "--cached", "--no-ext-diff", "--no-textconv", "--binary")),
        "unstaged_diff_sha256": digest(run("diff", "--no-ext-diff", "--no-textconv", "--binary")),
    }, []

def snapshot(workspace, names):
    workspace = Path(workspace).resolve()
    if not workspace.is_dir():
        raise ValueError("workspace must be an existing directory")
    hashes = {}
    for name in names:
        target, relative = selected_file(workspace, name)
        if relative in hashes:
            raise ValueError("duplicate selected file: " + relative)
        hashes[relative] = digest(target.read_bytes())
    git, limitations = git_state(workspace)
    return {"schema_version": 1, "observed_at": datetime.now(timezone.utc).isoformat(),
            "workspace": str(workspace), "git": git, "files": hashes, "limitations": limitations}

def compare(saved, workspace, allow_relocation=False):
    if not isinstance(saved, dict) or saved.get("schema_version") != 1:
        raise ValueError("unsupported snapshot schema")
    if not isinstance(saved.get("workspace"), str) or not isinstance(saved.get("files"), dict):
        raise ValueError("snapshot workspace/files missing or invalid")
    if "git" not in saved or not isinstance(saved.get("limitations"), list):
        raise ValueError("snapshot git/limitations missing or invalid")
    if saved["git"] is not None:
        keys = {"root", "workspace_from_root", "head", "branch", "status",
                "staged_diff_sha256", "unstaged_diff_sha256"}
        if not isinstance(saved["git"], dict) or not keys.issubset(saved["git"]):
            raise ValueError("snapshot Git fields missing or invalid")
    for name, value in saved["files"].items():
        if not isinstance(name, str) or not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise ValueError("invalid selected file or digest in snapshot")
    current = snapshot(workspace, list(saved["files"]))
    differences = []
    if current["workspace"] != saved["workspace"] and not allow_relocation:
        differences.append("workspace")
    if current["limitations"] != saved["limitations"]:
        differences.append("limitations")
    a, b = saved["git"], current["git"]
    if (a is None) != (b is None):
        differences.append("git")
    elif a is not None:
        for key in b:
            if key == "root" and allow_relocation:
                continue
            if a.get(key) != b[key]:
                differences.append("git." + key)
    for name, value in current["files"].items():
        if saved["files"][name] != value:
            differences.append("files." + name)
    return {"matched": not differences, "differences": differences,
            "relocation_allowed": allow_relocation,
            "scope": "selected file bytes and captured Git state; not test or semantic verification"}

def validate(text):
    # Ignore fenced WIP when parsing headings.
    lines, fence = [], None
    for line in text.splitlines():
        marker = re.match(r"^\s*(" + chr(96) + r"{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = (token[0], len(token))
            elif token[0] == fence[0] and len(token) >= fence[1]:
                fence = None
            continue
        if fence is None:
            lines.append(line)
    plain = "\n".join(lines)
    sections = {}
    matches = list(re.finditer(r"(?m)^## (.+?)\s*$", plain))
    for i, match in enumerate(matches):
        title = match.group(1)
        if title in sections:
            return {"valid": False, "errors": ["duplicate section: " + title]}
        sections[title] = plain[match.end():matches[i+1].start() if i+1 < len(matches) else len(plain)].strip()
    errors = ["missing or empty section: " + name for name in REQUIRED if not sections.get(name)]
    if re.search(r"(?im)(?:TODO|TBD|PLACEHOLDER|待填写|写出一个可执行动作|<workspace>|<relative-file>)", text):
        errors.append("unfinished template placeholder")
    if re.search(r"(?m)^\s*-\s*[^:\n]{1,80}[：:]\s*$", plain):
        errors.append("empty labeled template field")
    secret_patterns = {
        "private-key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "provider-token": r"\b(?:sk-(?:ant-)?[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b",
        "bearer": r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{12,}",
        "credential-assignment": r"(?im)\b(?:api[_-]?key|password|passwd|access[_-]?token)\b\s*[=:]\s*[\"']?(?!REDACTED|\*{3}|<)[^\s\"']{8,}",
    }
    for label, pattern in secret_patterns.items():
        if re.search(pattern, text):
            errors.append("probable secret: " + label)
    return {"valid": not errors, "errors": errors,
            "scope": "structure and common credential patterns only"}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("snapshot")
    capture.add_argument("--workspace", required=True)
    capture.add_argument("--file", action="append", default=[])
    capture.add_argument("--output", type=Path)
    check = commands.add_parser("check")
    check.add_argument("--snapshot", type=Path, required=True)
    check.add_argument("--workspace", required=True)
    check.add_argument("--allow-relocation", action="store_true")
    packet = commands.add_parser("validate")
    packet.add_argument("file", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "snapshot":
            result = snapshot(args.workspace, args.file)
            if args.output:
                with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                    json.dump(result, stream, ensure_ascii=True, indent=2)
                    stream.write("\n")
                result = {"created": str(args.output.resolve()), "schema_version": 1}
            code = 0
        elif args.command == "check":
            saved = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
            result = compare(saved, args.workspace, args.allow_relocation)
            code = 0 if result["matched"] else 1
        else:
            result = validate(args.file.read_text(encoding="utf-8-sig"))
            code = 0 if result["valid"] else 1
    except (OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
        result, code = {"error": str(exc)}, 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return code

if __name__ == "__main__":
    raise SystemExit(main())
