#!/usr/bin/env python3
"""Validate a persisted tech-mentor topic file.

The validator checks structure, explicit learning state, unfinished placeholders,
and likely secrets. It does not judge pedagogy or claim that learning occurred.
Standard library only; Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence


REQUIRED_H2 = ("目标", "类型", "路径", "检验标准", "学习状态")
STATUS_FIELDS = ("更新时间", "当前阶段", "未验证项", "下一步")
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>|\b(?:TODO|TBD|FIXME)\b", re.IGNORECASE)
SECRET_RE = re.compile(
    r"(?im)^\s*(?:api[_ -]?key|token|password|passwd|cookie|secret|私钥|密码)\s*[:=]\s*(\S+)"
)
DATE_RE = re.compile(r"(?m)^\s*-?\s*更新时间\s*[:：]\s*(\d{4}-\d{2}-\d{2})\s*$")


def finding(rule_id: str, severity: str, message: str) -> Dict[str, str]:
    return {"rule_id": rule_id, "severity": severity, "message": message}


def validate_text(text: str) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    if not re.search(r"(?m)^#\s+\S", text):
        findings.append(finding("TOPIC_MISSING_TITLE", "error", "缺少一级标题。"))

    headings = set(re.findall(r"(?m)^##\s+(.+?)\s*$", text))
    for heading in REQUIRED_H2:
        if heading not in headings:
            findings.append(
                finding("TOPIC_MISSING_SECTION", "error", f"缺少必需章节：## {heading}")
            )

    placeholders = PLACEHOLDER_RE.findall(text)
    if placeholders:
        sample = ", ".join(placeholders[:3])
        findings.append(
            finding("TOPIC_UNFINISHED_PLACEHOLDER", "error", f"仍有未完成占位符：{sample}")
        )

    status_match = re.search(r"(?ms)^##\s+学习状态\s*$\n(.*?)(?=^##\s+|\Z)", text)
    if status_match:
        status = status_match.group(1)
        for field in STATUS_FIELDS:
            if not re.search(rf"(?m)^\s*-?\s*{re.escape(field)}\s*[:：]\s*\S", status):
                findings.append(
                    finding("TOPIC_MISSING_STATUS_FIELD", "error", f"学习状态缺少字段：{field}")
                )
        date_match = DATE_RE.search(status)
        if date_match:
            try:
                date.fromisoformat(date_match.group(1))
            except ValueError:
                findings.append(
                    finding("TOPIC_INVALID_DATE", "error", "更新时间必须是有效的 YYYY-MM-DD。")
                )

    for match in SECRET_RE.finditer(text):
        value = match.group(1).strip().lower()
        if value not in {"redacted", "<redacted>", "***", "未保存", "无"}:
            findings.append(
                finding("TOPIC_POSSIBLE_SECRET", "error", "主题文件疑似包含凭据或秘密，请删除。")
            )
            break

    if len(text) > 12000:
        findings.append(
            finding(
                "TOPIC_CONTEXT_SIZE",
                "warn",
                f"主题文件为 {len(text)} 字符；考虑把历史练习归档，只保留当前状态和证据摘要。",
            )
        )
    return findings


def render_text(path: Path, findings: Sequence[Dict[str, str]]) -> str:
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warn" for item in findings)
    verdict = "FAIL" if errors else "PASS-WITH-WARNINGS" if warnings else "PASS"
    lines = [f"TOPIC VALIDATION: {verdict}", f"File: {path}", f"Errors: {errors}; warnings: {warnings}"]
    lines.extend(f"[{item['severity'].upper()}] {item['rule_id']}: {item['message']}" for item in findings)
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a tech-mentor topic markdown file.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    try:
        text = args.path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        parser.error(str(exc))
    findings = validate_text(text)
    errors = sum(item["severity"] == "error" for item in findings)
    if args.as_json:
        print(json.dumps({"file": str(args.path), "findings": findings}, ensure_ascii=False, indent=2))
    else:
        print(render_text(args.path, findings))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
