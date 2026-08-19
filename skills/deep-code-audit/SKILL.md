---
name: deep-code-audit
description: Perform evidence-backed, read-only audits of software repositories or scoped changes for correctness, security, maintainability, readability, state and data ownership, testability, performance, architecture, file organization, dependency risk, proportionate sensitive-data risk, accidental complexity, overengineering, and unnecessary implementation or change surface. Use for comprehensive codebase audits, security reviews, or deep review of a diff, branch, pull request, file, or subsystem. Do not use for dedicated bug reproduction or root-cause diagnosis, dependency-only reviews, personal-data or anonymization reviews, repository data-exposure audits, pre-addition supply-chain gates, routine implementation, simple style feedback, or a narrowly specified fix that does not request an audit.
license: MIT
---

# Deep Code Audit

Perform a non-mutating, coverage-aware audit. Report demonstrated risks and worthwhile improvements without turning preferences, scanner output, authorship guesses, or missing evidence into facts.

## Preserve the audit boundary

- Follow the user request and every applicable `AGENTS.md` before doing anything else.
- Treat activation as permission to inspect and report, not permission to edit application, test, configuration, documentation, or other user-authored repository files. Do not save an audit report unless the user explicitly requests one. Implement fixes only under a separate implementation request.
- Record `git status --short` before running checks and again before handoff. Also record the reviewed revision, requested comparison base, and the staged, unstaged, and untracked scope so the final comparison is meaningful.
- Do not run rewriting formatters, installations, upgrades, migrations, deployments, destructive commands, credentialed services, or unrelated external systems.
- Run repository-discovered, non-deploying tests, builds, linters, type checks, help commands, and already-configured scanners when they are safe. Build artifacts and caches are acceptable; unexpected tracked-file changes are not. Stop the responsible command and preserve the evidence after an unexpected mutation. Report every observed mutation, including expected artifact or cache paths, or state that none occurred.
- Never expose credentials or sensitive values. Redact values while preserving the file, line, category, and evidence needed to act.

## Select the audit mode and freeze repository truth

1. Read applicable instructions, manifests, lockfiles, entrypoints, public interfaces, schemas, tests, CI, deployment and runtime configuration, and useful history.
2. Establish the requested goal, success criteria, repository boundaries, supported environments, and compatibility constraints. Ask only material questions that repository inspection cannot answer.
3. Select the requested scope: whole repository, current Git changes, explicit base or range, branch, pull request, subsystem, file, or path set. Default an unqualified deep audit to the whole repository.
4. For current changes, inspect staged, unstaged, and untracked work relative to `HEAD`. If the repository is clean and the intended comparison base is ambiguous, ask for the base rather than inventing one.
5. Inspect callers, callees, tests, configuration, public contracts, and data flow outside a narrow scope when needed to judge impact. Keep findings scoped and distinguish change-introduced issues from relevant pre-existing issues.
6. Map first-party components, trust boundaries, external integrations, dependency boundaries, test strategy, and operational paths before drawing conclusions.
7. Recheck revision and dirty-state evidence while closing the audit. If in-scope content changed during review, do not mix snapshots: refresh affected ledger rows and evidence against the new state, or report the stale coverage and stop the affected conclusion.

## Establish the canonical coverage contract

Create one internal coverage ledger before review begins, whether work is local or delegated. Give every in-scope subsystem or changed behavior a stable ID such as `S01` and record:

- exact boundary;
- key files, interfaces, and tests;
- dependencies, callers, consumers, and operational paths;
- risk rationale;
- review depth;
- workflow state and owner;
- closure outcome, finding IDs, and gaps.

Use these independent dimensions:

- Workflow: `queued`, `reviewing`, `verifying`, or `closed`.
- Depth: `deep`, `sampled`, or `none`.
- Closure: `findings`, `no-finding`, `excluded`, or `blocked`.

For a whole-repository audit, cover every identifiable in-scope subsystem. For a scoped change, cover every changed behavior plus affected callers, contracts, tests, configuration, and data paths. Do not let a broad catch-all row hide distinct ownership or claim exhaustive review when sampling occurred.

Verify generated, vendored, binary, and build artifacts before excluding them. Prioritize authentication, authorization, untrusted input, parsers, persistence, filesystem, network and process access, public APIs, concurrency, secrets, deployment controls, complex state, weak tests, and central dependencies. Use file size, churn, complexity, duplication, test gaps, and dependency centrality as navigation signals, not automatic findings.

## Route the applicable review references

- Read [references/review-domains.md](references/review-domains.md) for source-code, test, architecture, performance, operability, data, state, or user-impact review.
- Read [references/security-review.md](references/security-review.md) when trust boundaries, authentication, authorization, untrusted input, secrets, sensitive operations, public interfaces, or AI-enabled behavior are in scope.
- Read [references/supply-chain.md](references/supply-chain.md) when manifests, lockfiles, CI actions, build plugins, containers, released artifacts, provenance, dependencies, or vulnerability evidence are in scope.
- Read [references/simplicity-and-change-quality.md](references/simplicity-and-change-quality.md) for source, test, architecture, diff, branch, or pull-request audits where implementation design, maintainability, accidental complexity, overengineering, or patch focus is material. Do not load it for a narrowly security-configuration-only audit unless implementation complexity also matters.
- Keep proportionate dependency-risk coverage in broad audits. Route a dependency-only review or pre-addition supply-chain gate to `$audit-dependencies` when that skill is available.
- Keep proportionate secret and sensitive-data coverage in broad audits. Route a dedicated personal-data, anonymization, repository-leak, or disposable-migration review to `$audit-data-exposure` when that skill is available.
- Broad audits may identify likely defects, but route dedicated reproduction, debugging, regression, or root-cause investigation to `$diagnose-bugs` when that skill is available.

## Run bounded review lanes

- Use subagents only for independent workstreams where parallel review materially improves coverage. Do not delegate merely because capacity exists.
- Keep no more than three subagents active concurrently, excluding the primary agent. A user instruction may lower, raise, or prohibit this limit; host limits still apply.
- Partition work by non-overlapping subsystem, attack surface, dependency group, or audit domain. Give each reviewer exact boundaries, relevant instructions, evidence requirements, and the same read-only and privacy constraints.
- Require each reviewer to return covered paths, depth, gaps, commands, candidate findings, confidence, and unresolved questions. An explicit no-finding result closes coverage when its evidence is adequate.
- Keep delegation under the primary agent's control. A delegated reviewer must not spawn another agent unless the user explicitly authorizes hierarchical delegation.
- Reassign or review bounded work locally when a reviewer fails or drifts. Work sequentially when subagents are unavailable, the scope is small, or partitioning would duplicate effort.

## Gather and control evidence

- Support consequential claims with paths and symbols, line references, commands and outputs, reproducible runtime results, history, or authoritative external sources.
- Label consequential context as `observed`, `inferred`, `assumed`, or `unknown/research-gated`. Do not label every sentence.
- Use current external research when public package versions, advisories, standards, licenses, or vendor behavior affect a decision. Prefer maintainers, standards bodies, official registries, and primary advisory databases; include URLs and access dates.
- Automatically transmit only public package names and versions for dependency research. Do not transmit private source, internal package coordinates, personal files, credentials, or sensitive repository data without explicit authorization.
- Treat scanner output as leads and supporting evidence. A clean scan does not prove security, and an installed vulnerable package does not by itself prove reachable exploitation.
- Compare conflicting evidence by authority, version, date, scope, methodology, configuration, and applicability. Do not choose silently.

## Verify and promote candidate findings

Track every candidate from `candidate` to `verifying`, then one terminal decision: `accepted`, `narrowed`, `demoted`, `rejected`, or `superseded`. Record the candidate ID, source reviewer, proposed owning subsystem, direct evidence, coordinator verification, decision rationale, and replacement finding when applicable.

- The primary agent must independently verify decision-critical evidence, confirm that it still matches the reviewed revision, and assign one authoritative subsystem.
- Treat `narrowed` as an accepted finding with reduced scope or classification. Treat `demoted` as an optional opportunity. Omit rejected and superseded candidates from the decision set, but retain enough internal trace to explain reconciliation when useful.
- Consolidate repeated manifestations of one root cause and list representative locations. Do not multiply one systemic problem into many findings.
- Promote every verified `critical` or `high` finding. Promote `medium` and `low` findings only when they materially change a decision or provide a worthwhile action. Keep lower-value verified work in a short optional backlog only when useful.
- Never cap credible urgent correctness or security findings. Never manufacture findings so that every subsystem produces one.

## Apply the simplicity and change-quality gate

- Establish required behavior, invariants, trust boundaries, compatibility promises, and operational constraints before judging code unnecessary.
- Review both the resulting implementation and the patch that produced it. A focused design can arrive through a diffuse patch, and a small patch can leave an unnecessarily complex design.
- Prefer the minimum semantic surface that completely and clearly satisfies evidenced requirements: fewer independent concepts, policies, states, branches, APIs, dependencies, configuration obligations, lifecycle responsibilities, and unrelated edits.
- For each material abstraction, mode, flag, layer, dependency, configuration option, cache, background process, public API, or persistent state, ask what evidenced requirement would fail without it.
- Search for an adequate repository, language, standard-library, platform, framework, or already-installed capability before accepting parallel machinery. Verify semantics, ownership, edge cases, compatibility, and security rather than assuming reuse is simpler.
- Prefer the smallest behaviorally complete change at the correct boundary. Do not reward a shorter textual patch that leaves sibling paths broken or transfers complexity into callers, configuration, types, reflection, builds, deployment, or operations.
- Do not optimize for minimum line, character, file, function, class, test, abstraction, or dependency counts. Preserve explicit security, accessibility, data-integrity, compatibility, lifecycle, protocol, concurrency, and recovery behavior unless a safer complete alternative is evidenced.
- Do not infer AI authorship from code style or use suspected authorship as evidence, severity, or disposition. Review observable residue, duplication, unsupported APIs, hidden dependencies, shallow tests, and patch diffusion without labeling the author.
- Report unnecessary complexity only when a concrete cost or failure path and a behaviorally complete alternative can be demonstrated. Otherwise omit it or mark the question `research-gated`.

## Classify and write findings

Assign four separate dimensions:

- Severity: `critical`, `high`, `medium`, or `low`, based on plausible impact and exposure.
- Confidence: `high`, `medium`, or `low`, based on evidence quality and reproducibility.
- Disposition: `required`, `recommended`, `optional`, or `research-gated`.
- Implementation order: `now`, `next`, `later`, or `backlog`, based on urgency, confidence, prerequisites, effort, blast radius, migration risk, and rollout constraints.

Use `critical` for credible immediate compromise, catastrophic data loss, or a release-blocking failure requiring urgent action. Use `high` for severe exploitable security, correctness, integrity, or availability risk. Use `medium` for a material defense, reliability, performance, testability, or maintainability risk with a realistic path. Use `low` for a contained weakness or worthwhile cleanup with demonstrated value.

Use this concrete shape for every reportable finding:

```markdown
### [Finding ID] [Consequence-oriented title]

- Owning subsystem:
- Affected location:
- Introduced by current change: yes | no | unknown
- Severity:
- Confidence:
- Disposition:
- Implementation order:

#### Observation and evidence
#### Failure, exploit, or change scenario
#### Root cause
#### Smallest credible remediation
#### Trade-offs and migration
#### Verification
#### Residual uncertainty
```

For a simplicity or change-quality finding, also identify the behavior and constraints to preserve, unnecessary surface, behaviorally complete alternative, equivalence evidence, and complexity transferred elsewhere. Do not use titles such as `too much code`, `AI slop`, `not DRY`, or `too many files`.

For dependency vulnerabilities, include the package and resolved version, advisory identifier, affected and fixed ranges, source URL, access date, and known reachability or exploitability limits. Keep package presence, vulnerable version, reachable path, and demonstrated exploitability separate.

## Validate and close the audit

Perform fresh passes before reporting:

1. Coverage: find missing boundaries, hidden catch-all rows, and unresolved rows.
2. Evidence: confirm accepted findings against the reviewed revision and separate observations from inference and unknowns.
3. Ownership: deduplicate root causes and give each finding one authoritative subsystem.
4. Materiality: reject preference-only recommendations and complexity that is merely relocated.
5. Classification: recalibrate severity, confidence, disposition, and order consistently.
6. Completeness: ensure each reportable finding has the required scenario, trade-offs, verification, and residual uncertainty.
7. Dependencies: make remediation prerequisites and ordering internally consistent.
8. Integrity: compare final repository state with the recorded initial state.

The audit is complete only when every coverage row is `closed` with depth, closure, and gaps recorded; every promoted finding has passed coordinator verification; duplicates and superseded findings are resolved; missing evidence is explicitly blocked or research-gated; and repository integrity has been checked. A blocked row closes accounting, not inspection, and must remain a stated limitation.

## Report economically

Lead with verified findings ordered by severity, confidence, and implementation order. Always include:

- requested scope, comparison base, reviewed revision, and initial repository state;
- a meaningful coverage summary with sampled, excluded, blocked, and unresolved areas;
- promoted findings, or a direct statement that none survived verification;
- checks and commands run, failures, all observed mutations or an explicit `none`, and unrun material checks;
- final repository-state comparison and limitations.

Include dependency research, external sources, systemic patterns, remediation ordering, candidate reconciliation, and subagent details only when applicable. Do not emit empty headings, repeat complete findings in an executive summary, or dump the review checklist into the report. Keep optional opportunities short and non-blocking. Never describe the audit as a penetration test or guarantee the absence of defects or vulnerabilities.
