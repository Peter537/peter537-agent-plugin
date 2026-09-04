---
name: verification-context
description: Create, assess, or maintain a repository's authoritative verification guidance from existing local evidence. Use only when the user explicitly invokes $verification-context to document verification commands, entrypoints, environments, fixtures, evidence limits, persistence boundaries, reset procedures, and cleanup. Do not use to execute acceptance verification, perform comprehensive documentation audits, plan unresolved behavior, add dependencies or harnesses, diagnose bugs, run one named check, or prepare a release.
license: MIT
---

# Repository Verification Context

Maintain durable project knowledge that a later verification run can consume without mistaking documentation for proof. Derive every entry from repository evidence, label its current validation state, and change only the exact context location the user authorizes.

## Preserve the ownership boundary

- Read applicable repository instructions and record the starting revision and Git state. Preserve every pre-existing staged, unstaged, and untracked change.
- Treat invocation as authorization for read-only assessment only. Update an existing verification artifact only when the request authorizes that artifact; create a new one only after the user approves its exact path.
- Do not make the context an acceptance authority. Record acceptance sources separately and quote no private values.
- Do not execute completed-change proof or assign an acceptance verdict; `$verify-change` consumes this guidance and establishes that evidence. A separately authorized, safely preflighted repository-native command may be exercised only to validate its invocation, side effects, and cleanup for the context. Do not diagnose or repair failures, plan unresolved product decisions, perform a comprehensive documentation audit, or prepare a release.
- Do not create tests, fixtures, browser hosts, telemetry, services, or project scaffolding. Never install packages, tools, workloads, or runtimes. Route a proposed addition through `$audit-dependencies`, which does not itself authorize installation.
- Do not contact shared or production systems, start a live service, upload repository content, or use private data without separate explicit authorization.

## Load focused guidance

- Read [authority-location-and-freshness.md](references/authority-location-and-freshness.md) before choosing a context location, resolving competing guidance, or assigning freshness.
- Read [verification-surfaces-and-evidence.md](references/verification-surfaces-and-evidence.md) when documenting commands, entrypoints, fixtures, persistence, or evidence layers.
- Read [safe-maintenance-and-handoff.md](references/safe-maintenance-and-handoff.md) before editing, considering a wrapper, handling authentication requirements, or reporting the result.

## Select the operation

- **Assess:** inventory the existing context, sources, conflicts, and gaps without writing.
- **Maintain:** create or update the exact authorized context artifact using verified repository evidence.
- **Thin wrapper:** only when the user separately authorizes the exact wrapper path, sequence already-authoritative commands using an existing runtime and propagate their exit status. Add no assertion, dependency, secret argument, environment mutation, or new verification behavior.

If no authoritative location exists, or equal-authority locations conflict, stop with `BLOCKED` and request approval for one exact path or an owner decision. Preserve an established format. For an approved new artifact, use concise Markdown unless the repository establishes another format; mandate no filename.

## Build an evidence-backed context

1. Establish the artifact's owner, audience, scope, authority, target revisions or variants, and authoritative acceptance sources.
2. Discover verification commands from repository instructions, scripts, manifests, CI, tests, and maintained documentation. Record each command as a direct argument sequence, its working directory, prerequisites, side effects, and validation state. Never invent or silently repair a command.
3. Record runnable entrypoints and readiness signals; environment and authentication requirements by variable, role, or credential class without values; deterministic fixture identity; persistence boundaries; reset procedure; cleanup owner; and known platform or build variants. Inspect the executable cleanup path rather than relying on its label: when a command recursively removes a parent directory, require that entire directory to be absent or wholly task-owned before execution, or classify the command as `blocked`.
4. Keep evidence layers separate: static or build, API, UI, persistence, operational or telemetry, and native. State what each surface can and cannot prove. A documented command is not execution evidence, a screenshot is not interaction evidence, and browser behavior is not native behavior.
5. Assign every consequential entry one state:
   - `verified-current`: exercised safely against the recorded revision during this task.
   - `discovered-unverified`: supported by a current repository authority but not run in this task.
   - `stale`: contradicted by newer authoritative repository evidence.
   - `blocked`: required evidence, access, identity, reset, or ownership cannot be established safely.
6. Record the last-verified revision only for entries actually verified at that revision. Use an explicit unverified marker for dirty-worktree observations rather than implying a commit contains them.
7. Reconcile documented side-effect and cleanup claims with the implementation of the command. Review links, protected literals, unrelated Git state, and the final diff. Do not remove stale guidance silently; replace it with the current entry or mark the conflict and required owner decision.

Keep the artifact compact and operational. Prefer a table or short sections when they make variants and evidence states easier to compare, but do not add headings merely for symmetry.

## Return one outcome

- `NO_CHANGE`: the authorized context is current, sufficient for its stated scope, and no edit is warranted.
- `REVIEWED`: assessment is complete or the user did not authorize a context edit.
- `CREATED`: an approved new context artifact or separately authorized thin wrapper was created at the exact path.
- `UPDATED`: an authorized existing context artifact or thin wrapper was updated.
- `BLOCKED`: authority, path approval, safe evidence, or required ownership is unavailable.

Lead with the outcome and changed files. Then summarize what is current, unverified, stale, or blocked; the repository evidence used; commands actually run; evidence limits; cleanup; and final Git state. Never present the context itself as proof that a change works.
