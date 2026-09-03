---
name: evidence-research
description: Conduct current, multi-source research with primary-source retrieval, contradiction checks, evidence grading, citations, and token-efficient synthesis. Use for open-ended investigations, due diligence, market or policy research, and questions where source quality or freshness can change the answer. For supplied-document-only summarization use research-summarizer; for a listed-company fundamental review use stock-analysis together with this skill for document acquisition.
license: MIT
metadata:
  derived_from: "affaan-m/ECC deep-research and iterative-retrieval"
  adapted_for: "Codex"
---

# Evidence Research

Build an answer that another analyst can audit. Optimize for decision value, source quality, and marginal information gained—not the number of links collected.

## Frame the investigation

- State the decision or question, scope, jurisdiction, and as-of date.
- Split broad questions into 3–6 subquestions. Identify the claims that would change the conclusion.
- Use reasonable defaults when the request is clear. Ask only when a missing choice would materially change the result.

## Route tools and sources

Before browser work, check for a purpose-built connector, local source, API, or CLI that can perform the semantic operation. Use available tools; never invent a connector or command.

Rank evidence:

1. Primary: regulator or government records, exchange filings, company filings, standards, court records, original datasets, source code, and original research.
2. First-party supporting material: investor relations, technical documentation, earnings calls, and official announcements.
3. Independent secondary analysis with transparent methods.
4. Aggregators, news summaries, blogs, forums, and social posts as leads or sentiment evidence—not the source of record.

For consequential claims, prefer one primary source plus an independent cross-check. If only one source exists, label the claim unverified.

## Retrieve progressively

1. Build a small query portfolio: exact term, synonym or acronym, relevant language variant, time-bounded query, and a disconfirming query.
2. Scan titles, snippets, metadata, and tables of contents first. Deduplicate mirrors, syndicated articles, and sources quoting the same upstream record.
3. Deep-read only the 3–5 sources most likely to decide the question. Expand when evidence conflicts or a critical gap remains.
4. For each useful source capture title, publisher, date, URL or file location, relevant section/page, claim supported, and any limitation.
5. Evaluate gaps and refine the query. Stop after at most three refinement passes unless the user explicitly asks for exhaustive coverage.

Stop when new sources mostly repeat known facts, all load-bearing claims have adequate evidence, contradictions are resolved or clearly bounded, and remaining uncertainty would not change the decision. State unresolved gaps instead of searching indefinitely.

## Analyze before synthesizing

- Separate sourced fact, calculation, inference, forecast, and opinion.
- Reconcile conflicting dates, units, definitions, consolidated/standalone bases, and revisions before comparing numbers.
- Apply a recency gate: identify the newest incorporated period and search for later events that could invalidate it.
- Seek the strongest credible counterevidence and explain whether it changes the conclusion.
- Grade evidence as High, Medium, or Low based on source tier, directness, cross-source agreement, recency, and methodological transparency.
- Do not convert absence of evidence into evidence of absence.

## Synthesize for decisions

Lead with the answer and confidence. Then provide:

- the few findings that determine the conclusion;
- evidence and citations adjacent to each material claim;
- contradictions, unknowns, and assumptions;
- the strongest alternative interpretation;
- what future evidence would confirm or falsify the conclusion;
- a concise source list and methodology note for substantial research.

Use tables only for repeated comparisons. Save a long evidence ledger or full report to a file only when the user requests a durable artifact or the material cannot fit clearly in chat.

## Financial routing

- Listed-company fundamentals, earnings quality, governance, valuation, forensic accounting, or IPO analysis: use `stock-analysis`; use this skill to acquire and cross-check current primary documents.
- Internal FP&A, ratios, DCF mechanics, forecasts, and budget variance: use `financial-analyst`.
- Never mix periods, units, currencies, or reporting bases. Every financial figure needs a source and period; current price and market cap need an as-of timestamp.

## Token and memory discipline

- Retrieve metadata and excerpts before full documents; avoid loading duplicate pages or entire repositories.
- Summarize each deep-read source into claims and evidence before opening the next one.
- Carry forward a compact evidence ledger rather than raw browsing output.
- Load only references relevant to the selected mode; do not restate source content already captured accurately.
- Treat time-sensitive facts as expiring. Store durable context only when the user asks or it is a stable project rule: preferences belong in Codex Memories, repository rules in `AGENTS.md`, and governed knowledge in project documentation.
- Never store secrets, credentials, sensitive financial data, or unverified claims as memory.

## Failure conditions

Do not claim comprehensive coverage when access is blocked, sources are paywalled, data is stale, or primary records are unavailable. Report the gap, its likely impact, and the exact document or access needed next.
