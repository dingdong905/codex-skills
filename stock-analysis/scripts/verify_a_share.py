#!/usr/bin/env python3
"""A-share intake gate layered on stock-analysis verify_data.py.

Checks that a CN A-share analysis explicitly covers the filings and governance
items that frequently carry the conclusion. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import verify_data as base  # noqa: E402


EXCHANGES = {"SSE", "SZSE", "BSE"}
BOARDS = {"main", "star", "chinext", "bse"}
STATUSES = {"checked", "not_available", "not_applicable"}
REQUIRED_CHECKS = (
    "audit_opinion",
    "non_recurring_items",
    "related_party_and_fund_occupation",
    "pledge_and_freeze",
    "regulatory_actions",
    "rd_capitalization",
    "major_restructuring_and_goodwill",
)
PRIMARY_SOURCE_RE = re.compile(
    r"cninfo\.com\.cn|sse\.com\.cn|szse\.cn|bse\.cn|csrc\.gov\.cn|巨潮|上交所|深交所|北交所|证监会|年报|半年报|季报|annual report|公告|问询函|处罚",
    re.IGNORECASE,
)


def add(rule_id: str, severity: str, message: str) -> base.Finding:
    return base.Finding(rule_id, severity, message)


def check_a_share(doc: Dict[str, Any]) -> List[base.Finding]:
    findings: List[base.Finding] = []
    profile = str(doc.get("market_profile") or "").upper()
    if profile != "CN-A":
        findings.append(add("A_SHARE_MARKET_PROFILE", base.SEVERITY_ERROR, "market_profile 必须为 CN-A。"))

    section = doc.get("a_share")
    if not isinstance(section, dict):
        return findings + [add("A_SHARE_SECTION_MISSING", base.SEVERITY_ERROR, "缺少 a_share 对象。")]

    exchange = str(section.get("exchange") or "").upper()
    if exchange not in EXCHANGES:
        findings.append(add("A_SHARE_EXCHANGE", base.SEVERITY_ERROR, "a_share.exchange 必须是 SSE、SZSE 或 BSE。"))
    board = str(section.get("board") or "").lower()
    if board not in BOARDS:
        findings.append(add("A_SHARE_BOARD", base.SEVERITY_ERROR, "a_share.board 必须是 main、star、chinext 或 bse。"))

    sources = section.get("primary_sources")
    if not isinstance(sources, list) or not sources:
        findings.append(add("A_SHARE_PRIMARY_SOURCES", base.SEVERITY_ERROR, "至少记录一份法定披露原件。"))
    else:
        has_annual = False
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                findings.append(add("A_SHARE_SOURCE_SHAPE", base.SEVERITY_ERROR, f"primary_sources[{index}] 必须是对象。"))
                continue
            source_type = str(source.get("type") or "")
            locator = str(source.get("source") or source.get("url") or "")
            if source_type == "annual_report":
                has_annual = True
            for field in ("type", "period", "published"):
                if not source.get(field):
                    findings.append(add("A_SHARE_SOURCE_FIELD", base.SEVERITY_ERROR, f"primary_sources[{index}] 缺少 {field}。"))
            if not locator:
                findings.append(add("A_SHARE_SOURCE_LOCATOR", base.SEVERITY_ERROR, f"primary_sources[{index}] 缺少 source 或 url。"))
            elif not PRIMARY_SOURCE_RE.search(locator):
                findings.append(add("A_SHARE_SOURCE_UNCONFIRMED", base.SEVERITY_WARN, f"primary_sources[{index}] 看不出来自交易所、巨潮或法定公告：{locator}"))
        if not has_annual:
            findings.append(add("A_SHARE_ANNUAL_REPORT", base.SEVERITY_ERROR, "primary_sources 必须包含 type=annual_report。"))

    checks = section.get("checks")
    if not isinstance(checks, dict):
        return findings + [add("A_SHARE_CHECKS_MISSING", base.SEVERITY_ERROR, "缺少 a_share.checks 对象。")]

    for name in REQUIRED_CHECKS:
        item = checks.get(name)
        if not isinstance(item, dict):
            findings.append(add("A_SHARE_CHECK_MISSING", base.SEVERITY_ERROR, f"缺少专属检查：{name}"))
            continue
        status = str(item.get("status") or "")
        if status not in STATUSES:
            findings.append(add("A_SHARE_CHECK_STATUS", base.SEVERITY_ERROR, f"{name}.status 必须是 checked、not_available 或 not_applicable。"))
            continue
        if status == "checked":
            source = str(item.get("source") or "")
            if not source or not item.get("result"):
                findings.append(add("A_SHARE_CHECK_EVIDENCE", base.SEVERITY_ERROR, f"{name} 已标为 checked，但缺少 source 或 result。"))
            elif not PRIMARY_SOURCE_RE.search(source):
                findings.append(add("A_SHARE_CHECK_SOURCE", base.SEVERITY_WARN, f"{name} 的来源看不出是一手披露：{source}"))
        elif not item.get("reason"):
            findings.append(add("A_SHARE_CHECK_REASON", base.SEVERITY_ERROR, f"{name} 标为 {status} 时必须说明 reason。"))
        elif status == "not_available":
            severity = base.SEVERITY_ERROR if name == "audit_opinion" else base.SEVERITY_WARN
            findings.append(add("A_SHARE_CHECK_UNAVAILABLE", severity, f"{name} 尚无可靠底稿：{item['reason']}"))

    has_ttm = any(
        isinstance(item, dict) and re.search(r"\b(?:TTM|LTM)\b", str(item.get("period") or ""), re.IGNORECASE)
        for item in doc.get("datapoints", [])
    )
    if has_ttm:
        bridge = section.get("ttm_bridge")
        required = ("full_year", "current_ytd", "prior_ytd", "basis")
        if not isinstance(bridge, dict) or any(not bridge.get(field) for field in required):
            findings.append(
                add(
                    "A_SHARE_TTM_BRIDGE",
                    base.SEVERITY_ERROR,
                    "存在 TTM/LTM 数据，但缺少 full_year + current_ytd - prior_ytd 及统一 basis 的桥接记录。",
                )
            )
    return findings


TEMPLATE = {
    "company": "",
    "ticker": "",
    "as_of": "YYYY-MM-DD",
    "reporting_basis": "consolidated",
    "currency": "CNY",
    "units": "million",
    "fiscal_year_end": "December",
    "latest_reported_period": {"period": "FY2025", "published": "YYYY-MM-DD"},
    "market_profile": "CN-A",
    "datapoints": [],
    "not_available": [],
    "a_share": {
        "exchange": "SSE",
        "board": "main",
        "primary_sources": [
            {"type": "annual_report", "period": "FY2025", "published": "YYYY-MM-DD", "url": "https://..."}
        ],
        "ttm_bridge": {
            "full_year": "FY2025",
            "current_ytd": "H1 2026",
            "prior_ytd": "H1 2025",
            "basis": "consolidated; same currency, units and restatement basis"
        },
        "checks": {
            name: {"status": "not_available", "reason": "待取得法定披露"}
            for name in REQUIRED_CHECKS
        },
    },
}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a CN A-share stock-analysis intake.")
    parser.add_argument("input", nargs="?")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--template", action="store_true")
    args = parser.parse_args(argv)
    if args.template:
        print(json.dumps(TEMPLATE, ensure_ascii=False, indent=2))
        return 0
    if not args.input:
        parser.error("an intake JSON file is required (or use --template)")
    try:
        doc = base.load_intake(args.input)
    except ValueError as exc:
        parser.error(str(exc))
    findings = base.verify(doc) + check_a_share(doc)
    findings.sort(key=lambda item: (base._SEVERITY_RANK.get(item.severity, 9), item.rule_id))
    if args.as_json:
        print(base.render_json(doc, findings))
    else:
        print(base.render_text(doc, findings))
    return 1 if base.counts(findings)[base.SEVERITY_ERROR] else 0


if __name__ == "__main__":
    raise SystemExit(main())
