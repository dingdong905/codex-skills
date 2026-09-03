---
name: context-budget
description: Audit and reduce Codex context and token overhead across instructions, skills, tools, MCP servers, retrieval, and memory. Use when sessions feel bloated, too much material is being loaded, many integrations overlap, or the user asks to save tokens without sacrificing answer quality. Do not use for pricing or production LLM API cost architecture.
license: MIT
metadata:
  derived_from: "affaan-m/ECC context-budget and strategic-compact"
  adapted_for: "Codex"
---

# Context Budget

Produce a read-only, evidence-based context audit. Optimize the information path before shortening task-critical instructions.

## Inventory

Inspect only what is available and relevant:

- global and repository `AGENTS.md` files;
- user and repository skills, distinguishing metadata from bodies and references;
- configured MCP servers, plugins, and exposed tool schemas;
- duplicated rules, prompts, templates, and memory/context documents;
- retrieval behavior: whole-file reads, repeated searches, duplicate sources, and oversized tool outputs.

Codex uses progressive disclosure for skills: metadata is discoverable up front, while `SKILL.md`, references, and scripts load on demand. Do not count every installed skill body as always-loaded context.

## Measure without false precision

Use an available tokenizer when practical. Otherwise label estimates and use consistent approximations such as characters divided by four for English/code-heavy text; note that Chinese and structured schemas can differ materially.

Separate:

- always-present instructions and tool schemas;
- conditionally loaded skill bodies and references;
- task-specific retrieved content and conversation history;
- durable memory or project context.

Report counts, estimated tokens, overlap, trigger breadth, and confidence. Do not invent context-window size, cache behavior, or per-tool overhead.

## Diagnose

Classify components as:

- Keep: frequently needed, unique, and concise.
- Lazy-load: useful but domain- or phase-specific.
- Merge: materially duplicated guidance or source content.
- Retire candidate: stale, unused, incompatible, or fully superseded.

Flag especially:

- broad skill descriptions that trigger unrelated work;
- duplicate rules across global and project files;
- large MCP surfaces used for one or two operations;
- whole-document or whole-repository reads before relevance filtering;
- repeated raw outputs retained after their claims are summarized;
- the same fact stored in Memories, `AGENTS.md`, and project docs;
- time-sensitive memories without an as-of date or expiry signal.

## Optimize in impact order

1. Disable or avoid unused tool/MCP surfaces; prefer a purpose-built connector or CLI for the current operation.
2. Narrow skill descriptions and merge overlapping skills while preserving unique workflows.
3. Keep `AGENTS.md` small; move conditional details to routed skill references.
4. Retrieve progressively: search metadata/snippets, rank relevance, then deep-read decisive files or sources.
5. Replace bulky raw history with a compact phase summary, evidence ledger, or implementation handoff at logical boundaries.
6. Deduplicate stable context across memory layers.
7. Shorten wording only after structural waste is removed. Preserve safety, correctness, source, and authorization constraints.

## Memory placement

- Codex Memories: stable user preferences and useful cross-chat personal context.
- `AGENTS.md`: durable repository rules that should apply before work begins.
- Project documentation: reviewed decisions, architecture, runbooks, and authoritative knowledge.
- Task notes or evidence ledgers: temporary state with an as-of date and a clear expiry or closure condition.

Do not promote a one-off correction, unverified claim, secret, credential, private key, or sensitive personal/financial information into durable memory. Ask before writing or changing any persistent context.

## Output

Lead with estimated overhead and the three highest-value changes. Include a compact breakdown, evidence for each finding, expected savings as a range, quality risks, and a reversible action plan.

The audit is read-only by default. Do not delete skills, disable tools, edit configuration, or rewrite memory unless the user explicitly asks for those changes. After any approved change, remeasure the same components and report the observed delta.
