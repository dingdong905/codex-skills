#!/usr/bin/env python3
"""统一学术元数据检索、规范化、去重和标识符核验。仅依赖标准库。"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
USER_AGENT = "codex-skills-research-toolkit/1.0 (public academic metadata client)"
TIMEOUT = 25


class ResearchError(RuntimeError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def clean_doi(value: Any) -> str | None:
    value = text_or_none(value)
    if not value:
        return None
    value = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", value, flags=re.I)
    return value.strip().lower() or None


def base_record(source: str, **values: Any) -> dict[str, Any]:
    record = {
        "title": None,
        "authors": [],
        "year": None,
        "published": None,
        "venue": None,
        "identifiers": {},
        "abstract": None,
        "record_type": "work",
        "peer_review_status": "unknown",
        "citation_count": None,
        "open_access": {"is_oa": None, "url": None, "status": "unknown"},
        "is_retracted": None,
        "urls": [],
        "sources": [source],
        "provenance": {"source": source, "source_id": None, "fetched_at": now_utc()},
    }
    for key, value in values.items():
        if value is not None:
            record[key] = value
    return record


def request_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                raise ResearchError(f"HTTP {exc.code}: {url}") from exc
            retry_after = exc.headers.get("Retry-After")
            delay = min(float(retry_after), 10.0) if retry_after and retry_after.isdigit() else float(2 ** attempt)
            time.sleep(delay)
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == 2:
                raise ResearchError(f"网络请求失败: {exc.reason}") from exc
            time.sleep(float(2 ** attempt))
    raise ResearchError(f"网络请求失败: {last_error}")


def request_json(url: str) -> dict[str, Any]:
    try:
        return json.loads(request_bytes(url).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResearchError(f"上游返回了无法解析的 JSON: {url}") from exc


def strip_markup(value: Any) -> str | None:
    value = text_or_none(value)
    if not value:
        return None
    value = re.sub(r"<[^>]+>", " ", value)
    return text_or_none(" ".join(html.unescape(value).split()))


def inverted_abstract(index: Any) -> str | None:
    if not isinstance(index, dict):
        return None
    positioned: list[tuple[int, str]] = []
    for word, positions in index.items():
        if isinstance(positions, list):
            positioned.extend((int(position), str(word)) for position in positions)
    positioned.sort()
    return " ".join(word for _, word in positioned) or None


def openalex_record(item: dict[str, Any]) -> dict[str, Any]:
    ids = item.get("ids") or {}
    location = item.get("primary_location") or {}
    source = location.get("source") or {}
    oa = item.get("open_access") or {}
    doi = clean_doi(ids.get("doi") or item.get("doi"))
    identifiers = {"doi": doi} if doi else {}
    if doi and doi.startswith("10.48550/arxiv."):
        identifiers["arxiv"] = doi.split("arxiv.", 1)[1]
    for candidate in [location.get("landing_page_url"), location.get("pdf_url")]:
        match = re.search(r"arxiv\.org/(?:abs|pdf)/([^/?#]+)", candidate or "", flags=re.I)
        if match:
            identifiers["arxiv"] = re.sub(r"(?:\.pdf)?v\d+$", "", match.group(1), flags=re.I)
            break
    urls = [value for value in [item.get("id"), ids.get("doi"), location.get("landing_page_url"), location.get("pdf_url")] if value]
    return base_record(
        "openalex",
        title=text_or_none(item.get("display_name") or item.get("title")),
        authors=[a.get("author", {}).get("display_name") for a in item.get("authorships", []) if a.get("author", {}).get("display_name")],
        year=item.get("publication_year"),
        published=item.get("publication_date"),
        venue=source.get("display_name"),
        identifiers=identifiers,
        abstract=inverted_abstract(item.get("abstract_inverted_index")),
        record_type=item.get("type") or "work",
        peer_review_status="preprint" if item.get("type") == "preprint" else "unknown",
        citation_count=item.get("cited_by_count"),
        open_access={"is_oa": oa.get("is_oa"), "url": oa.get("oa_url"), "status": oa.get("oa_status") or "unknown"},
        is_retracted=item.get("is_retracted"),
        urls=list(dict.fromkeys(urls)),
        provenance={"source": "openalex", "source_id": item.get("id"), "fetched_at": now_utc()},
    )


def search_openalex(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"search": query, "per-page": limit})
    payload = request_json(f"https://api.openalex.org/works?{params}")
    return [openalex_record(item) for item in payload.get("results", [])]


def search_openalex_by_doi(doi: str) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"filter": f"doi:{doi}", "per-page": 1})
    payload = request_json(f"https://api.openalex.org/works?{params}")
    return [openalex_record(item) for item in payload.get("results", [])]


def search_arxiv_via_openalex(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({
        "search": query,
        "filter": "primary_location.source.id:S4306400194",
        "per-page": limit,
    })
    payload = request_json(f"https://api.openalex.org/works?{params}")
    records = [openalex_record(item) for item in payload.get("results", [])]
    for record in records:
        record["provenance"]["fallback_from"] = "arxiv"
    return records


def crossref_record(item: dict[str, Any]) -> dict[str, Any]:
    title_value = item.get("title") or []
    container = item.get("container-title") or []
    date_parts = ((item.get("published-print") or item.get("published-online") or item.get("issued") or {}).get("date-parts") or [[]])[0]
    published = "-".join(str(part) for part in date_parts) if date_parts else None
    authors = []
    for author in item.get("author") or []:
        name = " ".join(part for part in [author.get("given"), author.get("family")] if part)
        if name:
            authors.append(name)
    doi = clean_doi(item.get("DOI"))
    links = item.get("link") or []
    fulltext_url = next((link.get("URL") for link in links if link.get("content-version") == "vor"), None)
    urls = [value for value in [item.get("URL"), f"https://doi.org/{doi}" if doi else None, fulltext_url] if value]
    return base_record(
        "crossref",
        title=text_or_none(title_value[0] if title_value else None),
        authors=authors,
        year=date_parts[0] if date_parts else None,
        published=published,
        venue=text_or_none(container[0] if container else None),
        identifiers={"doi": doi} if doi else {},
        abstract=strip_markup(item.get("abstract")),
        record_type=item.get("type") or "work",
        peer_review_status="unknown",
        citation_count=item.get("is-referenced-by-count"),
        open_access={"is_oa": None, "url": None, "status": "unknown"},
        is_retracted=None,
        urls=list(dict.fromkeys(urls)),
        provenance={"source": "crossref", "source_id": doi, "fetched_at": now_utc()},
    )


def search_crossref(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"query.bibliographic": query, "rows": limit})
    payload = request_json(f"https://api.crossref.org/works?{params}")
    return [crossref_record(item) for item in payload.get("message", {}).get("items", [])]


def pubmed_xml_records(xml_bytes: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    records = []
    for article in root.findall(".//PubmedArticle"):
        citation = article.find("MedlineCitation")
        journal_article = citation.find("Article") if citation is not None else None
        if citation is None or journal_article is None:
            continue
        pmid = text_or_none(citation.findtext("PMID"))
        title = "".join(journal_article.find("ArticleTitle").itertext()) if journal_article.find("ArticleTitle") is not None else None
        abstract_parts = ["".join(node.itertext()) for node in journal_article.findall("Abstract/AbstractText")]
        authors = []
        for author in journal_article.findall("AuthorList/Author"):
            name = " ".join(part for part in [author.findtext("ForeName"), author.findtext("LastName")] if part)
            if name:
                authors.append(name)
        journal = journal_article.find("Journal")
        venue = journal.findtext("Title") if journal is not None else None
        pubdate = journal.find("JournalIssue/PubDate") if journal is not None else None
        year_text = pubdate.findtext("Year") if pubdate is not None else None
        medline_date = pubdate.findtext("MedlineDate") if pubdate is not None else None
        year_match = re.search(r"\d{4}", year_text or medline_date or "")
        year = int(year_match.group()) if year_match else None
        identifiers: dict[str, str] = {}
        if pmid:
            identifiers["pmid"] = pmid
        doi = None
        pmcid = None
        for article_id in article.findall("PubmedData/ArticleIdList/ArticleId"):
            kind = article_id.attrib.get("IdType")
            if kind == "doi":
                doi = clean_doi(article_id.text)
            elif kind == "pmc":
                pmcid = text_or_none(article_id.text)
        if doi:
            identifiers["doi"] = doi
        if pmcid:
            identifiers["pmcid"] = pmcid
        pubtypes = [node.text or "" for node in journal_article.findall("PublicationTypeList/PublicationType")]
        lowered = " ".join(pubtypes).lower()
        is_retracted = True if "retracted publication" in lowered else None
        status = "preprint" if "preprint" in lowered else "unknown"
        urls = [f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"] if pmid else []
        if doi:
            urls.append(f"https://doi.org/{doi}")
        if pmcid:
            urls.append(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/")
        records.append(base_record(
            "pubmed",
            title=text_or_none(title),
            authors=authors,
            year=year,
            published=year_text or medline_date,
            venue=text_or_none(venue),
            identifiers=identifiers,
            abstract=text_or_none("\n".join(abstract_parts)),
            record_type="; ".join(pubtypes) if pubtypes else "journal article",
            peer_review_status=status,
            citation_count=None,
            open_access={"is_oa": True if pmcid else None, "url": urls[-1] if pmcid else None, "status": "pmc" if pmcid else "unknown"},
            is_retracted=is_retracted,
            urls=urls,
            provenance={"source": "pubmed", "source_id": pmid, "fetched_at": now_utc()},
        ))
    return records


def fetch_pubmed_ids(ids: list[str]) -> list[dict[str, Any]]:
    if not ids:
        return []
    params = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "xml"})
    return pubmed_xml_records(request_bytes(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}"))


def search_pubmed(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"db": "pubmed", "term": query, "retmax": limit, "retmode": "json"})
    payload = request_json(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}")
    return fetch_pubmed_ids(payload.get("esearchresult", {}).get("idlist", []))


def arxiv_records(xml_bytes: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_bytes)
    ns = {"a": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    records = []
    for entry in root.findall("a:entry", ns):
        url = text_or_none(entry.findtext("a:id", namespaces=ns))
        arxiv_id = re.sub(r"v\d+$", "", url.rsplit("/", 1)[-1]) if url else None
        published = text_or_none(entry.findtext("a:published", namespaces=ns))
        updated = text_or_none(entry.findtext("a:updated", namespaces=ns))
        authors = [text_or_none(node.findtext("a:name", namespaces=ns)) for node in entry.findall("a:author", ns)]
        pdf_url = next((link.attrib.get("href") for link in entry.findall("a:link", ns) if link.attrib.get("type") == "application/pdf"), None)
        doi = clean_doi(entry.findtext("arxiv:doi", namespaces=ns))
        identifiers = {}
        if arxiv_id:
            identifiers["arxiv"] = arxiv_id
        if doi:
            identifiers["doi"] = doi
        records.append(base_record(
            "arxiv",
            title=text_or_none(" ".join((entry.findtext("a:title", default="", namespaces=ns)).split())),
            authors=[author for author in authors if author],
            year=int(published[:4]) if published and published[:4].isdigit() else None,
            published=published,
            venue=text_or_none(entry.findtext("arxiv:journal_ref", namespaces=ns)),
            identifiers=identifiers,
            abstract=text_or_none(" ".join((entry.findtext("a:summary", default="", namespaces=ns)).split())),
            record_type="preprint",
            peer_review_status="preprint",
            citation_count=None,
            open_access={"is_oa": True, "url": pdf_url or url, "status": "green"},
            is_retracted=None,
            urls=[value for value in [url, pdf_url, f"https://doi.org/{doi}" if doi else None] if value],
            provenance={"source": "arxiv", "source_id": arxiv_id, "fetched_at": now_utc(), "updated": updated},
        ))
    return records


def search_arxiv(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"search_query": f"all:{query}", "start": 0, "max_results": limit, "sortBy": "submittedDate", "sortOrder": "descending"})
    return arxiv_records(request_bytes(f"https://export.arxiv.org/api/query?{params}"))


def clinical_trial_record(study: dict[str, Any]) -> dict[str, Any]:
    protocol = study.get("protocolSection") or {}
    identification = protocol.get("identificationModule") or {}
    status = protocol.get("statusModule") or {}
    design = protocol.get("designModule") or {}
    sponsor = protocol.get("sponsorCollaboratorsModule") or {}
    description = protocol.get("descriptionModule") or {}
    nct = identification.get("nctId")
    start = (status.get("startDateStruct") or {}).get("date")
    phases = design.get("phases") or []
    overall = status.get("overallStatus")
    url = f"https://clinicaltrials.gov/study/{nct}" if nct else None
    return base_record(
        "clinicaltrials",
        title=text_or_none(identification.get("briefTitle") or identification.get("officialTitle")),
        authors=[sponsor.get("leadSponsor", {}).get("name")] if sponsor.get("leadSponsor", {}).get("name") else [],
        year=int(start[:4]) if start and start[:4].isdigit() else None,
        published=start,
        venue="ClinicalTrials.gov",
        identifiers={"nct": nct} if nct else {},
        abstract=text_or_none(description.get("briefSummary")),
        record_type="clinical trial registration" + (f" ({', '.join(phases)})" if phases else ""),
        peer_review_status="registry",
        citation_count=None,
        open_access={"is_oa": True, "url": url, "status": "registry"},
        is_retracted=None,
        urls=[url] if url else [],
        provenance={"source": "clinicaltrials", "source_id": nct, "fetched_at": now_utc(), "overall_status": overall},
    )


def search_clinicaltrials(query: str, limit: int) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({"query.term": query, "pageSize": limit, "format": "json"})
    payload = request_json(f"https://clinicaltrials.gov/api/v2/studies?{params}")
    return [clinical_trial_record(study) for study in payload.get("studies", [])]


SEARCHERS = {
    "openalex": search_openalex,
    "crossref": search_crossref,
    "pubmed": search_pubmed,
    "arxiv": search_arxiv,
    "clinicaltrials": search_clinicaltrials,
}


def normalize_title(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(char for char in text if char.isalnum())


def record_keys(record: dict[str, Any]) -> list[str]:
    ids = record.get("identifiers") or {}
    keys = [f"{kind}:{str(value).casefold()}" for kind, value in ids.items() if value]
    title = normalize_title(record.get("title"))
    if title:
        keys.append(f"title:{title}:{record.get('year') or ''}")
    return keys


def merge_records(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    merged = dict(left)
    for field in ["title", "year", "published", "venue", "record_type", "peer_review_status", "citation_count"]:
        if merged.get(field) in (None, "", [], "unknown") and right.get(field) not in (None, "", [], "unknown"):
            merged[field] = right[field]
    if len(right.get("abstract") or "") > len(merged.get("abstract") or ""):
        merged["abstract"] = right["abstract"]
    if len(right.get("authors") or []) > len(merged.get("authors") or []):
        merged["authors"] = right["authors"]
    merged["identifiers"] = {**(merged.get("identifiers") or {}), **(right.get("identifiers") or {})}
    merged["urls"] = list(dict.fromkeys((merged.get("urls") or []) + (right.get("urls") or [])))
    merged["sources"] = list(dict.fromkeys((merged.get("sources") or []) + (right.get("sources") or [])))
    left_oa = merged.get("open_access") or {}
    right_oa = right.get("open_access") or {}
    if right_oa.get("is_oa") is True and left_oa.get("is_oa") is not True:
        merged["open_access"] = right_oa
    if right.get("is_retracted") is True:
        merged["is_retracted"] = True
    elif merged.get("is_retracted") is None and right.get("is_retracted") is False:
        merged["is_retracted"] = False
    return merged


def deduplicate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    index: dict[str, int] = {}
    for record in records:
        match = next((index[key] for key in record_keys(record) if key in index), None)
        if match is None:
            match = len(output)
            output.append(record)
        else:
            output[match] = merge_records(output[match], record)
        for key in record_keys(output[match]):
            index[key] = match
    return output


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    normalized = base_record((record.get("sources") or ["unknown"])[0])
    normalized.update({key: value for key, value in record.items() if key in normalized})
    normalized["identifiers"] = {str(key).lower(): value for key, value in (normalized.get("identifiers") or {}).items() if value}
    if normalized["identifiers"].get("doi"):
        normalized["identifiers"]["doi"] = clean_doi(normalized["identifiers"]["doi"])
    normalized["authors"] = [str(author).strip() for author in normalized.get("authors") or [] if str(author).strip()]
    normalized["urls"] = list(dict.fromkeys(str(url) for url in normalized.get("urls") or [] if url))
    normalized["sources"] = list(dict.fromkeys(str(source) for source in normalized.get("sources") or [] if source))
    return normalized


def load_records(path: str) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    records = payload.get("records", []) if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not all(isinstance(record, dict) for record in records):
        raise ResearchError("输入必须是 record 数组，或包含 records 数组的对象")
    return records


def envelope(operation: str, records: list[dict[str, Any]], query: dict[str, Any] | None = None, warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": operation,
        "query": query or {},
        "fetched_at": now_utc(),
        "records": records,
        "warnings": warnings or [],
    }


def verify(identifier_type: str, identifier: str) -> tuple[list[dict[str, Any]], list[str]]:
    if identifier_type == "doi":
        doi = clean_doi(identifier)
        if not doi:
            raise ResearchError("DOI 为空")
        payload = request_json(f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}")
        record = crossref_record(payload["message"])
        warnings = []
        try:
            openalex_records = search_openalex_by_doi(doi)
            if openalex_records:
                record = merge_records(record, openalex_records[0])
            else:
                warnings.append("OpenAlex 未返回此 DOI；撤稿与开放获取状态仍可能未知。")
        except ResearchError as exc:
            warnings.append(f"OpenAlex 状态交叉核验失败：{exc}")
        return [record], warnings
    if identifier_type == "pmid":
        return fetch_pubmed_ids([identifier]), []
    if identifier_type == "arxiv":
        clean_id = re.sub(r"^arxiv:", "", identifier, flags=re.I)
        params = urllib.parse.urlencode({"id_list": clean_id})
        try:
            return arxiv_records(request_bytes(f"https://export.arxiv.org/api/query?{params}")), []
        except ResearchError as exc:
            if "HTTP 429" not in str(exc):
                raise
            records = search_openalex_by_doi(f"10.48550/arxiv.{clean_id}")
            for record in records:
                record["provenance"]["fallback_from"] = "arxiv"
            return records, ["arXiv API 返回 429；使用 OpenAlex 按 arXiv DOI 回退，正式引用前需再次核验版本。"]
    if identifier_type == "nct":
        nct = identifier.upper()
        payload = request_json(f"https://clinicaltrials.gov/api/v2/studies/{urllib.parse.quote(nct, safe='')}")
        return [clinical_trial_record(payload)], []
    raise ResearchError(f"不支持的标识符类型: {identifier_type}")


def write_output(payload: dict[str, Any], output: str | None) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2)
    if output:
        Path(output).write_text(content + "\n", encoding="utf-8")
    else:
        print(content)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("--provider", choices=sorted(SEARCHERS), required=True)
    search_parser.add_argument("--query", required=True)
    search_parser.add_argument("--limit", type=int, default=10)
    search_parser.add_argument("--output")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--id-type", choices=["doi", "pmid", "arxiv", "nct"], required=True)
    verify_parser.add_argument("--identifier", required=True)
    verify_parser.add_argument("--output")
    for command in ["normalize", "dedupe"]:
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("--input", required=True)
        command_parser.add_argument("--output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "search":
            if not 1 <= args.limit <= 100:
                raise ResearchError("limit 必须在 1 到 100 之间")
            warnings = []
            try:
                records = SEARCHERS[args.provider](args.query, args.limit)
            except ResearchError as exc:
                if args.provider != "arxiv" or "HTTP 429" not in str(exc):
                    raise
                records = search_arxiv_via_openalex(args.query, args.limit)
                warnings.append("arXiv API 返回 429；本次使用 OpenAlex 的 arXiv 来源过滤结果回退，需在引用前再次核验 arXiv 记录。")
            result = envelope(
                "search",
                deduplicate(records),
                {"provider": args.provider, "text": args.query, "limit": args.limit},
                warnings,
            )
        elif args.command == "verify":
            records, warnings = verify(args.id_type, args.identifier)
            if not records:
                raise ResearchError("未找到匹配记录")
            result = envelope("verify", records, {"id_type": args.id_type, "identifier": args.identifier}, warnings)
        elif args.command == "normalize":
            result = envelope("normalize", [normalize_record(record) for record in load_records(args.input)])
        else:
            result = envelope("dedupe", deduplicate([normalize_record(record) for record in load_records(args.input)]))
        write_output(result, args.output)
        return 0
    except (ResearchError, ET.ParseError, KeyError, OSError, json.JSONDecodeError) as exc:
        print(f"researchctl: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
