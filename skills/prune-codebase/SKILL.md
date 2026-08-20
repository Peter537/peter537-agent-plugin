---
name: prune-codebase
description: Prove and safely retire dead or obsolete repository surface, including unused symbols, files, exports, routes, handlers, assets, flags, experiments, shims, compatibility paths, and migration paths. Use for clear requests to find or remove dead code, retire obsolete behavior, clean up stale feature flags or migrations, or prune a codebase. Do not use for broad code audits, local C# or Python simplification, dependency removal, bug diagnosis, architecture redesign, feature work, or cleanup justified only by style.
license: MIT
---

# Evidence-Driven Codebase Pruning

Reduce maintenance surface only after proving what is live, what is obsolete, and which consumers or lifecycle obligations still matter. An analyzer result is a candidate, not permission to delete.

## Preserve scope and authority

- Read applicable repository instructions and record the initial Git state. Preserve unrelated staged, unstaged, and untracked work.
- Treat a review, inventory, or "find dead code" request as read-only.
- For a broad cleanup request, report stable candidate IDs and wait for the user to approve specific IDs or batches before editing.
- A precise removal or edit request that names symbols, files, paths, flags, or retirement work authorizes only those targets. A review remains read-only even when it names exact targets. Re-verify every authorized target immediately before changing it.
- Previously approved candidate IDs remain usable only against the same repository state and evidence boundary. Reclassify a candidate when relevant code, configuration, consumers, or lifecycle state changed.
- Do not install analyzers, packages, runtimes, workloads, or tools. Use repository-native tools only when they are already configured and can run without deployments or external mutations.
- Do not remove dependencies or edit manifests or lockfiles under this skill. Route dependency removal through `$audit-dependencies` when available.
- Do not query or mutate external feature-flag systems or other remote control planes automatically. Read-only access requires explicit authorization for the exact service, destination, and data; mutation remains a separate authorized operation. Do not mutate production data, databases, deployments, remote APIs, or compatibility commitments. Executing a migration or operational retirement requires separate explicit authorization.
- Keep private source and diagnostics local by default. Redact secrets, customer data, internal endpoints, and sensitive runtime evidence from reports.

## Keep the capability boundary clear

This skill owns evidence and retirement for repository surface whose absence is intended: unused symbols or files, unreachable handlers, obsolete routes, retired flags or experiments, expired shims, unsupported compatibility paths, completed migration paths, and equivalent maintenance surface.

- Route a comprehensive repository audit to `$deep-code-audit`.
- Route behavior-preserving simplification of surviving C# or Python code to `$reduce-code-slop`.
- Route dependency or package removal to `$audit-dependencies`.
- Route uncertain architecture or compatibility-retirement design to `$deep-planning`.
- Route a concrete failing behavior to `$diagnose-bugs`.
- Route personal-data or disposable data-conversion review to `$audit-data-exposure`.

Do not turn ordinary indirection, boilerplate, repeated syntax, or an unfamiliar abstraction into a pruning candidate merely because it looks removable. Do not infer authorship or use "slop" as a finding.

## Load only the relevant guidance

- Read [references/liveness-entrypoints-and-tooling.md](references/liveness-entrypoints-and-tooling.md) before classifying code, files, exports, routes, handlers, assets, or generated surface.
- Read [references/operational-retirement.md](references/operational-retirement.md) for flags, experiments, shims, compatibility paths, API versions, migrations, rollout code, or stateful retirement.
- Read [references/knowledge-drift-and-policy.md](references/knowledge-drift-and-policy.md) when apparently duplicated constants, rules, mappings, schemas, or policy knowledge are in scope.
- Read [references/approval-verification-and-reporting.md](references/approval-verification-and-reporting.md) before presenting a broad candidate set or applying any approved removal.

## Establish the evidence boundary

1. Identify the requested scope, revision or comparison base, supported products, entrypoints, workspaces, public surfaces, environments, and build or deployment variants.
2. Inspect manifests, project files, build scripts, CI matrices, packaging and deployment configuration, tests, runtime registration, generated-code inputs, and useful history.
3. Map consumers beyond direct static references: reflection, serialization, dependency injection, plugins, dynamic imports, route or command discovery, convention-loaded files, templates, native bindings, side-effect initialization, and externally consumed APIs.
4. Identify lifecycle evidence for flags, experiments, shims, compatibility paths, migrations, and old versions. Code can be statically reachable yet obsolete, or statically unreachable yet contractually required.
5. Record coverage gaps such as unavailable build variants, missing generated inputs, shallow history, inaccessible downstream repositories, absent telemetry, offline services, or uninitialized submodules.

Observed execution proves a path is live for the observed scenario. Lack of observed execution does not prove it is dead. Search results prove only what the searched representation and revision contain.

## Build and verify candidates

Assign stable IDs such as `PC-001` and retain them through review and authorized follow-up. For each candidate, record:

- repository location and owning subsystem;
- surface type and proposed coherent removal batch;
- static and dynamic liveness evidence;
- lifecycle or obsolescence evidence when applicable;
- entrypoints, variants, public or external consumers, and generated behavior checked;
- missing consumers or configurations;
- concrete maintenance consequence;
- risk, confidence, verification plan, and residual uncertainty.

Classify each candidate as one of:

- `ready`: evidence supports removal within the established boundary, no material consumer or lifecycle obligation remains, and a proportionate verification path exists.
- `needs-decision`: removal depends on product, compatibility, retention, rollout, ownership, or operational policy that repository evidence cannot decide.
- `keep`: evidence shows the surface is live, contractually required, intentionally reserved, generated, or justified.
- `research-gated`: a material coverage gap prevents a trustworthy liveness or lifecycle conclusion.

Do not promote a candidate solely because a tool reports it, a text search finds no references, tests do not cover it, telemetry does not observe it, a flag has one apparent branch, or code is old. When evidence conflicts, narrow the claim or use `needs-decision` or `research-gated`.

Duplicated knowledge is in scope only when repository evidence shows that the copies express one authoritative rule that must evolve together. Coincidental equal values, protocol-required constants, independent bounded contexts, test expectations, and intentionally duplicated deployment artifacts are not automatically pruning candidates.

## Apply only an authorized coherent batch

After approval or a precise removal request:

1. Recheck the revision, Git state, candidate evidence, consumers, lifecycle state, and relevant configuration.
2. Run the smallest trustworthy existing baseline checks when feasible. Separate pre-existing failures from task-created regressions.
3. Remove one reachability chain or retirement concept per coherent batch, including only tests, documentation, registrations, configuration, and assets whose sole contract is the approved retired behavior.
4. Never weaken or delete a test merely to make the removal pass. A failing test may be evidence that the behavior is still required or that the approved batch is incomplete.
5. Recompute affected reachability and candidate classifications after each batch. A deletion can expose new dead surface or reveal a previously hidden consumer.
6. Run the same checks and relevant neighboring checks, inspect packaging or build outputs where applicable, review the final diff, and compare the final Git state with the initial state.

Stop and return to the user if re-verification changes an approved candidate, deletion would cross into an unapproved dependency, external system, data migration, or compatibility commitment, or the remaining verification cannot distinguish safe retirement from breakage.

## Return one outcome

- `NO_CHANGE`: an authorized prune request completed without removal because no approved target survived re-verification or the target was live or required.
- `REVIEWED`: a read-only review completed with classified candidates or a verified no-candidate result.
- `PRUNED`: an approved coherent batch was removed and relevant checks passed.
- `BLOCKED`: essential scope, consumer, lifecycle, permission, or safe verification evidence was unavailable.

Lead with the outcome. Include scope and revision, classified candidate IDs or applied batches, decisive evidence, coverage gaps, checks, observed mutations, final repository state, unrun checks, and residual uncertainty. Describe the concrete maintenance or failure consequence; never claim that a repository is free of dead code or that removal is safe beyond the evidence boundary.
