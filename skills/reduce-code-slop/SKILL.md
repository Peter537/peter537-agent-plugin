---
name: reduce-code-slop
description: Simplify explicitly scoped C# or Python code without changing its established behavior. Use for clear requests to remove unnecessary indirection or generated boilerplate, harden weak type handling, de-slop an implementation, perform a focused simplification review, or apply already-configured simplification enforcement. Do not use for broad repository audits, bug diagnosis, architecture migrations, feature development, formatting-only cleanup, dependency installation, UI or prose work, or other languages.
license: MIT
---

# Evidence-Driven Code Simplification

Reduce demonstrated implementation cost while preserving the behavior and constraints the repository actually depends on. Never infer how code was authored or use "slop" as a finding; describe the concrete problem instead.

## Preserve scope and authority

- Read applicable repository instructions and record the initial Git state. Preserve unrelated staged, unstaged, and untracked work.
- Treat a review request as read-only. Edit only when the user requests simplification or refactoring, and only within the authorized scope.
- Do not install or introduce analyzers, packages, runtimes, workloads, or tools. Route any proposed addition through `$audit-dependencies` when that skill is available.
- Do not weaken tests, broaden suppressions, swallow failures, replace errors with success-like defaults, or perform mass cleanup to make the result look simpler.
- Use repository-native, already-installed tests, builds, type checks, and linters. Do not run rewriting tools unless the user authorized their exact output scope.
- Keep private source and diagnostics local by default. Redact secrets and sensitive values from reports.

## Select one mode

- **Focused review:** inspect the requested C# or Python scope and report verified simplification opportunities without editing.
- **Refactor:** make the smallest coherent behavior-preserving change requested by the user.
- **Enforcement:** run, or adjust the configuration of, an already-configured repository tool only when the user explicitly requests enforcement work. Missing tooling is a gap, not permission to install it.

If the request is a broad codebase assessment, route it to `$deep-code-audit`. Route concrete failure reproduction and causal repair to `$diagnose-bugs`, architecture or migration design to `$deep-planning`, dependency changes to `$audit-dependencies`, interface design to `$ui-design-and-polish`, and prose-only work to `$write-clearly` when those skills are available. Do not claim support for languages other than C# and Python.

## Load only the relevant guidance

- Read [references/behavior-evidence-and-completion.md](references/behavior-evidence-and-completion.md) before accepting a candidate or making a change.
- Read [references/csharp.md](references/csharp.md) for C# work.
- Read [references/python.md](references/python.md) for Python work.
- For a mixed C# and Python boundary, read both language references and preserve the cross-language contract explicitly.

## Establish the behavior boundary

Inspect the authorized implementation, callers, tests, configuration, public and serialized contracts, runtime or framework conventions, generated-code boundaries, and useful history. Record the behavior and constraints that must remain stable, including as applicable:

- public APIs, accepted inputs, outputs, and data formats;
- exceptions, diagnostics, fallback behavior, and observability;
- ordering, side effects, state transitions, and persistence;
- async, cancellation, concurrency, resource ownership, disposal, and lifetimes;
- compatibility promises, reflection or serialization names, framework discovery, and test seams.

If the required behavior cannot be established safely, stay read-only and return `BLOCKED` rather than guessing.

## Verify candidates before acting

Track each material candidate through `candidate -> verifying -> accepted | narrowed | rejected | exempted`.

- Start from a demonstrated cost or risk: hidden failure, unreliable type evidence, duplicated policy, unnecessary indirection, unclear ownership, unsupported compatibility machinery, or a wider change surface than the requirement needs.
- Test the counterfactual: identify what evidenced requirement would fail if the surface were removed or replaced.
- Require a behaviorally complete alternative at the correct boundary. Fewer lines or types are not evidence of a simpler system when complexity moves into callers, configuration, reflection, deployment, or operations.
- Preserve justified dynamic dispatch, reflection, explicit state machines, security controls, compatibility layers, generated code, serialization behavior, test seams, and framework-required indirection.
- Reject preference-only observations and syntax-pattern matches that lack a concrete consequence. Exempt justified complexity and record the evidence briefly when it prevents repeated churn.

For review mode, report only accepted or narrowed candidates. For refactor mode, implement only accepted candidates that fit the user's authorized scope and form one coherent change.

## Change and verify proportionately

1. Run the smallest trustworthy existing checks before editing when feasible. A green baseline supports behavior-preservation claims; a failing baseline must remain distinguished from task-created regressions.
2. Make the minimum coherent change. Do not bundle formatting, renaming, dependency work, new architecture, or unrelated cleanup.
3. Re-run the same checks and relevant neighboring checks after editing. Verify public and serialized contracts, error behavior, ownership, async or lifetime behavior, and framework integration where affected.
4. Review the final diff and Git state. Remove temporary artifacts and report unexpected mutations or unrun material checks.

Do not manufacture a failing test for a behavior-preserving refactor. Prefer green-before/green-after evidence, targeted characterization tests already justified by the request, or an explicit statement that equivalence could not be fully demonstrated.

## Report one outcome

- `NO_CHANGE`: an authorized refactor or enforcement request completed without an edit because no verified opportunity justified one.
- `REVIEWED`: the requested read-only review completed with verified findings or a verified no-finding result.
- `SIMPLIFIED`: an authorized simplification was completed and the relevant behavior checks passed.
- `BLOCKED`: essential behavior, access, tooling, or safe verification was unavailable.

Lead with the result and material outcome. Include the reviewed or changed scope, preserved behavior, accepted findings or edits, evidence and checks, final repository state, unrun checks, and residual uncertainty. Describe concrete consequences and trade-offs; never score "slop," speculate about authorship, or claim equivalence beyond the evidence.
