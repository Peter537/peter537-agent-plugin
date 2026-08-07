---
name: chatgpt-research
description: Orchestrate reproducible, multi-source software and product research through ChatGPT Deep Research and verify the resulting evidence. Use for complex or ambiguous questions requiring synthesis across external sources, official-documentation comparison, vendor or standards evaluation, UI reference analysis, conflicting claims, or traceable capture sets with URLs, dates, and citations. Do not use for a single fact, one-document lookup, ordinary web search, or repository-only investigation.
compatibility: Requires ChatGPT Deep Research and signed-in in-app Browser control; designed for ChatGPT and Codex.
---

# ChatGPT Research

Operate as a read-only research orchestrator for software and product decisions. Use actual ChatGPT Deep Research only when the question warrants multi-step external synthesis, verify its important evidence, and return the handoff in conversation.

## Preserve boundaries and authorization

- Do not create, modify, move, or delete local or repository files.
- Limit external mutations to starting or steering authorized ChatGPT Deep Research conversations. Do not post, submit, or change data on other external systems.
- Treat explicit `$chatgpt-research` invocation or a direct request for ChatGPT Deep Research as authorization to submit the non-sensitive research topic to `chatgpt.com`.
- When this skill is selected implicitly, explain why Deep Research is warranted and obtain confirmation before submitting anything to `chatgpt.com`.
- Do not transmit private repository content, personal files, credentials, sensitive data, or browsing history. Do not upload files or use connected ChatGPT apps unless the user explicitly authorizes that exact data and destination.
- Prefer primary and official sources. Use secondary sources for context or independent corroboration.

## Define the research contract

Before launching research, establish:

- the question and the software or product decision it informs;
- the audience and requested deliverable;
- the timeframe, versions, geography, and other scope boundaries;
- required, preferred, excluded, or connected sources;
- what evidence would materially change the decision; and
- the required depth, citation detail, and completion criteria.

Resolve discoverable facts through inspection. Ask no more than three material questions per round, and ask only when the answer changes scope, sources, privacy, cost, or the decision.

## Choose the right research depth

Do not start ChatGPT Deep Research for one fact, one known document, a direct URL, a narrow current-information lookup, or repository-only investigation. Use ordinary search, official documentation, or direct browser inspection for those tasks.

Use ChatGPT Deep Research when the task requires several subquestions or source classes, conflict resolution, controlled-source selection, or substantive synthesis across external evidence.

Use direct Browser capture instead of Deep Research when the main task is exact extraction from one interactive page.

## Launch ChatGPT Deep Research

1. Use the signed-in in-app Browser and actual `chatgpt.com`. Read and follow the current Browser skill before interacting.
2. If the in-app Browser is unavailable or cannot access the signed-in session, stop and ask before using Chrome or another browser. Do not bypass authentication with ordinary web search.
3. Inspect fresh visible UI state. Locate the current Deep Research control semantically; do not hardcode language-specific labels, positional selectors, or stale UI structure.
4. Create one dedicated ChatGPT conversation for each research job and submit a prompt containing the complete research contract.
5. Review ChatGPT's proposed plan for scope, sources, timeframe, and output. Start it when aligned. Route material deviations or new product choices to the user before starting.
6. Run one job by default. Split only independent, non-overlapping subquestions, and never run more than two jobs for one request.
7. Record each stable conversation URL, title, topic, and start time in a progress update. Retain the tab binding while it remains valid.

If ChatGPT asks a clarification that is already answered by the research contract, answer within that contract. Route new user-intent or disclosure decisions back to the user.

## Monitor and recover

- Monitor live progress and completion notifications for no more than 30 minutes from submission.
- Use bounded, non-blocking checks. Do not use fixed sleeps longer than 60 seconds, and provide progress updates at the cadence required by the host.
- Between checks, review known authoritative sources, establish decision criteria, inspect relevant repository context, prepare the evidence matrix, or monitor the second independent job. Do not start overlapping work merely to fill time.
- Interrupt or steer a job when visible progress drifts from the approved contract. Do not silently expand scope.
- If a tab becomes stale or closes, reopen the saved conversation URL in the in-app Browser and verify the title, topic, and state before continuing.
- Never restart a duplicate job because completion is slow or the tab binding was lost.
- When a job remains incomplete after 30 minutes, report its last observed state and URL. Keep the running tab as a browser `handoff`.
- When a report completes, keep its tab as a browser `deliverable` and close intermediate research or source tabs after extracting what is needed.

## Verify the report

Treat ChatGPT's report as synthesis and source discovery, not as an original source. Open and validate every decision-critical citation plus a representative sample of supporting claims.

For each consequential claim, record the applicable status:

- `supported`: one credible source directly supports the claim.
- `corroborated`: multiple independent credible sources support the claim.
- `inferred`: the conclusion is synthesized rather than directly stated.
- `unresolved/conflicted`: evidence is missing, inaccessible, or materially inconsistent.

Record primary or secondary source type separately. Capture the source title, publisher, direct URL, publication or update date when available, access date, applicable version and scope, short supporting context, and access limitations.

Verify quotation accuracy and compare conflicts by authority, date, version, methodology, and scope. Preserve counterexamples and unresolved conflicts instead of choosing silently.

## Handle interactive and raw captures

- For expandable, filtered, paginated, or dynamically loaded content, operate the exact visible controls and verify each state change before extracting data.
- Preserve complete content, original order, labels, counts, filters, and coverage only when the user explicitly requested a raw capture and the capture is permitted by copyright and source limits.
- Do not paraphrase within an explicit raw capture. Otherwise prefer faithful paraphrases and short quotations.
- When visual layout or state matters, capture the minimum screenshot evidence needed to verify it.
- Before completion, reconcile requested coverage, expanded state, counts, ordering, filters, source contents, and the resulting report.

## Return the handoff

Adapt the final format to the request, but always include:

- the conclusion or recommendation and its decision implications;
- consequential claims with research status and direct evidence links;
- publication or update dates and access dates;
- conflicts, counterexamples, access limitations, and remaining gaps;
- reproducibility steps; and
- every ChatGPT Deep Research conversation URL used.

For capture sets, also report coverage, expanded-state evidence, counts, ordering, filters, and source/report agreement.

Return everything in conversation. Never create a local research artifact.
