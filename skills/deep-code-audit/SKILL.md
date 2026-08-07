---
name: deep-code-audit
description: Perform evidence-backed audits of software repositories or explicitly scoped changes for correctness, security, maintainability, readability, testability, performance, architecture, file organization, and dependency risk. Use for comprehensive codebase audits, security reviews, dependency reviews, or deep review of a diff, branch, pull request, file, or subsystem. Do not use for routine implementation, simple style feedback, or a narrowly specified fix that does not request an audit.
---

# Deep Code Audit

Perform a non-mutating, coverage-aware audit. Report demonstrated risks and worthwhile improvements without turning preferences, scanner output, or missing evidence into facts.

## Preserve the audit boundary

- Follow the user request and every applicable `AGENTS.md` before doing anything else.
- Treat activation as permission to inspect and report, not permission to edit application, test, configuration, documentation, or other user-authored repository files. Do not save an audit report unless the user explicitly requests one. Implement fixes only under a separate implementation request.
- Record `git status --short` before running checks and again before handoff. Preserve all existing user work.
- Do not run rewriting formatters, installations, upgrades, migrations, deployments, destructive commands, credentialed services, or unrelated external systems.
- Run repository-discovered, non-deploying tests, builds, linters, type checks, help commands, and already-configured scanners when they are safe. Build artifacts and caches are acceptable; unexpected tracked-file changes are not. Stop the responsible command, preserve the evidence, and report any unexpected mutation.
- Never expose credentials or secret values. Redact values while preserving the file, line, secret type, and evidence needed to act.

## Establish scope and repository truth

1. Read applicable instructions, manifests, lockfiles, entrypoints, public interfaces, schemas, tests, CI, deployment and runtime configuration, and useful history.
2. Establish the requested goal, success criteria, repository boundaries, supported environments, and compatibility constraints. Ask only material questions that repository inspection cannot answer.
3. Default an unqualified deep audit to the whole repository.
4. For current Git changes, inspect staged, unstaged, and untracked work relative to `HEAD`. Use an explicit base, range, pull request, path, or subsystem when supplied. If the repository is clean and a comparison base is ambiguous, ask for the base rather than inventing one.
5. Inspect callers, callees, tests, configuration, public contracts, and data flow outside a narrow scope when needed to judge impact. Keep findings scoped and label relevant pre-existing issues separately from change-introduced issues.
6. Map first-party components, trust boundaries, external integrations, dependency boundaries, test strategy, and operational paths before drawing conclusions.

## Build a coverage and risk inventory

- Inventory all in-scope first-party areas before prioritizing review depth.
- Classify each area as `deep-reviewed`, `sampled`, `excluded`, or `blocked`, with a reason. Never claim exhaustive review unless every in-scope area was demonstrably inspected to that depth.
- Verify generated, vendored, binary, and build artifacts before excluding them.
- Prioritize authentication, authorization, untrusted input, parsers, persistence, filesystem/network/process access, public APIs, concurrency, secrets, deployment controls, complex or highly coupled code, weak tests, and dependency boundaries.
- Use file size, churn, complexity, duplication, test gaps, and dependency centrality as navigation signals, not automatic findings.
- Read [references/review-domains.md](references/review-domains.md) for any source-code or test audit. Read [references/security-supply-chain.md](references/security-supply-chain.md) for whole-repository, security, dependency, configuration, CI, or public-interface audits. Apply only relevant domains.

## Coordinate subagents deliberately

- Use subagents only for independent workstreams where parallel review materially improves coverage. Do not delegate merely because capacity exists.
- Keep no more than three subagents active concurrently, excluding the primary agent. A user instruction may lower, raise, or prohibit this limit; host limits still apply.
- Permit later batches after earlier agents finish, but avoid repeated delegation that adds no meaningful coverage.
- Keep delegation under the primary agent's control. If acting as a delegated subagent, do not spawn another agent unless the user explicitly authorizes hierarchical delegation.
- Partition work by non-overlapping subsystem, attack surface, dependency group, or audit domain. Give each agent explicit paths or questions, repository instructions, evidence requirements, and the same read-only and privacy constraints.
- Require each agent to return reviewed paths, coverage gaps, commands run, evidence, candidate findings, confidence, and unresolved questions.
- Independently verify decision-critical evidence. Reconcile conflicts, deduplicate overlaps, normalize severity, and remain accountable for the final report. Never present an unverified subagent claim as established fact.
- If an agent fails or drifts, reassign the bounded work or review it locally. Mark remaining gaps `blocked` or `research-gated`.
- Work sequentially when subagents are unavailable, the scope is small, or partitioning would duplicate effort.

## Gather and control evidence

- Support consequential claims with paths and symbols, line references, commands and outputs, reproducible runtime results, history, or authoritative external sources.
- Label consequential context as `observed`, `inferred`, `assumed`, or `unknown/research-gated`. Do not label every sentence.
- Use current external research when public package versions, advisories, standards, licenses, or vendor behavior affect a decision. Prefer maintainers, standards bodies, official registries, and primary advisory databases; include URLs and access dates.
- Automatically transmit only public package names and versions for dependency research. Do not transmit private source, internal package coordinates, personal files, credentials, or sensitive repository data without explicit authorization.
- Treat scanner output as leads and supporting evidence. A clean scan does not prove that a system is secure, and an installed vulnerable package does not by itself prove reachable exploitation.
- Compare conflicting evidence by authority, version, date, scope, methodology, configuration, and applicability. Do not choose silently.

## Make recommendations proportionate

- Prefer demonstrated correctness, security, operability, testability, and maintenance outcomes over theoretical cleanliness.
- Treat file length as a signal. Recommend splitting, merging, moving, or deleting only when responsibility, cohesion, change coupling, dependency direction, ownership, navigation, or test isolation supports it.
- Consider performance, compatibility, operational cost, and regression risk before recommending a more testable or abstract design.
- Verify dependency usage before recommending removal. Compare maintenance and security cost, standards complexity, edge cases, transitive weight, and available platform functionality before proposing custom replacement code.
- Never recommend replacing mature cryptography, authentication, authorization, security, parsing, serialization, or protocol code merely to reduce package count.
- Do not report style preferences as defects. Put low-value ideas in a short optional-opportunities section or omit them.

## Classify findings

Assign severity by plausible impact and exposure:

- `P0`: credible immediate compromise, catastrophic data loss, or release-blocking failure requiring urgent action.
- `P1`: severe exploitable security, correctness, integrity, or availability risk.
- `P2`: material defense gap, reliability, performance, testability, or maintainability risk with a realistic failure path.
- `P3`: contained low-impact weakness or worthwhile cleanup with demonstrated value.

Also assign:

- Confidence: `high`, `medium`, or `low`, based on evidence quality and reproducibility.
- Disposition: `required`, `recommended`, `optional`, or `research-gated`.

For every finding include:

1. Stable ID, category, concise title, affected location, and whether it is change-introduced or pre-existing.
2. Severity, confidence, disposition, direct evidence, and clearly separated inference or assumptions.
3. A concrete exploit, failure, maintenance, performance, or usability scenario and its affected boundary.
4. Remediation direction plus compatibility, performance, testability, and operational tradeoffs.
5. A specific verification method.
6. For dependency vulnerabilities, the package and installed version, advisory identifier, affected and fixed ranges, source URL, access date, and known reachability or exploitability limits.

Do not inflate severity because a category sounds dangerous. Do not lower severity merely because exploitation was not attempted.

## Report the audit

Lead with findings ordered by severity and confidence. Then include:

1. Executive summary and decision implications.
2. Requested scope, comparison base, repository state, and audit limitations.
3. Coverage inventory with deep-reviewed, sampled, excluded, and blocked areas.
4. Prioritized findings and a separate concise optional-opportunities section.
5. Dependency and supply-chain results when applicable.
6. Systemic patterns and recommended action order, including dependencies between remediations.
7. Commands and scanners run, results, failures, and unexpected mutations.
8. External sources with access dates, unresolved evidence, and research gates.
9. Subagent assignments, returned coverage, verification performed by the primary agent, and remaining gaps.
10. Final `git status --short` comparison demonstrating whether repository state changed.

If no findings survive verification, say so directly while still reporting coverage and limitations. Never describe an audit as a penetration test or guarantee the absence of vulnerabilities.
