#!/usr/bin/env python3
"""Adapted BM25 retrieval and schemas from claudekit design snapshot; stdlib only."""
import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "data/domains.json").read_text(encoding="utf-8"))

def tokenize(text):
    return re.findall(r"\w+", str(text).casefold())

def search(query, domain, limit=3):
    if domain not in CONFIG:
        raise ValueError(f"Unknown domain: {domain}")
    if not 1 <= limit <= 20:
        raise ValueError("limit must be from 1 to 20")
    config = CONFIG[domain]
    file = ROOT / "data" / config["file"]
    with file.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = set(config["search_cols"] + config["output_cols"] + ["No"])
        if not required <= set(reader.fieldnames or []):
            raise ValueError(f"Missing columns in {file.name}: {sorted(required - set(reader.fieldnames or []))}")
        rows = list(reader)
    terms = tokenize(query)
    docs = [tokenize(" ".join(row[col] for col in config["search_cols"])) for row in rows]
    average = sum(map(len, docs)) / max(len(docs), 1)
    frequencies = Counter(word for doc in docs for word in set(doc))
    matches = []
    if terms and average:
        for index, doc in enumerate(docs):
            counts, score = Counter(doc), 0.0
            for term in terms:
                tf = counts[term]
                if not tf: continue
                idf = math.log(1 + (len(docs) - frequencies[term] + 0.5) / (frequencies[term] + 0.5))
                score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * len(doc) / average))
            if score > 0:
                matches.append((score, index))
    # Exact canonical names outrank related variants; otherwise use BM25 relevance.
    identity = config["output_cols"][0]
    matches.sort(key=lambda item: (tokenize(rows[item[1]][identity]) != terms, -item[0], item[1]))
    results = [{"id": rows[index]["No"], **{col: rows[index][col] for col in config["output_cols"]}} for _, index in matches[:limit]]
    return {"domain": domain, "query": query, "source": config["file"], "count": len(results), "results": results}

def main(argv=None):
    parser=argparse.ArgumentParser(description="Read-only local design recommendations; no API or image generation")
    parser.add_argument("query")
    parser.add_argument("--domain", choices=list(CONFIG), help="Omit to search all domains for a brief")
    parser.add_argument("--max-results", "-n", type=int, choices=range(1,21), default=3, metavar="1-20")
    parser.add_argument("--brand", default=None, help="User-provided brand label; does not alter brand facts")
    parser.add_argument("--json", action="store_true")
    args=parser.parse_args(argv)
    try:
        output={"query":args.query,"brand":args.brand,"guidance_only":True,"domains":[search(args.query,d,args.max_results) for d in ([args.domain] if args.domain else CONFIG)]}
    except (OSError,ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr);return 1
    if args.json:
        print(json.dumps(output,ensure_ascii=False,indent=2))
    else:
        if args.brand: print(f"Design references for {args.brand}")
        for result in output["domains"]:
            print(f"{result['domain']}: {result['count']} matches ({result['source']})")
            for row in result["results"]:
                print(json.dumps(row,ensure_ascii=False))
        print("Recommendations only; verify fit with the user's brief and existing brand.")
    return 0

if __name__=="__main__":
    sys.exit(main())
