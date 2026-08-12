# Feedback loops and localization

Use this reference to create evidence that faithfully represents the reported defect and to narrow where correct behavior first diverges.

## Method anchors

- [Google SRE: Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) describes hypothesis-driven troubleshooting, system-boundary inspection, severity-aware triage, and avoiding correlation errors.
- [Stack Overflow: Minimal, Reproducible Example](https://stackoverflow.com/help/minimal-reproducible-example) defines minimal, complete, and reproducible problem examples.
- [Git: git bisect](https://git-scm.com/docs/git-bisect) documents binary-searching between known-good and known-bad revisions, including automated predicates.

Use these as methodological inputs. Adapt them to repository evidence rather than imposing another project's phases or tools.

## Signal selection ladder

Prefer the smallest authentic signal the repository can already support:

1. Existing focused test that demonstrates the exact symptom.
2. New regression test at an existing stable seam.
3. Repository-native CLI, request, browser, or integration workflow with a precise assertion.
4. Replay of a sanitized real input, event, trace, or fixture through the relevant path.
5. Differential comparison of the same input across working and failing states.
6. Property, fuzz, stress, or repetition loop with a preserved seed or schedule.
7. Bisection predicate for commits, configuration, dependencies, data, or test order.
8. Minimal disposable harness when it still exercises the real implementation boundary.
9. Structured human observation when automation is unavailable; record exact steps and observable acceptance conditions.

Reject a signal that is red only because setup, mocks, malformed fixtures, missing services, or unrelated assertions fail. Confirm symptom equivalence explicitly.

## Reduction discipline

- Change one input, step, configuration value, dependency, or state element at a time.
- Re-run the signal after every reduction and record whether the failure signature remains equivalent.
- Retain interactions, ordering, concurrency, lifecycle, and data relationships that are required for the defect.
- Stop reducing when further simplification changes the signature, removes the production path, or creates an artificial failure.
- Keep sanitized failing inputs only when appropriate for the repository; otherwise keep them local and ephemeral.

## Localization methods

- Compare working versus failing inputs, old versus new versions, clean versus existing environments, or one configuration versus another.
- Trace boundary inputs, outputs, state, timing, and configuration through callers and consumers.
- Find the earliest incorrect value or transition, then follow it backward toward its producer.
- Split a component or request path at stable interfaces and test each half with controlled input.
- Determine whether the failure belongs to implementation, test, fixture, environment, toolchain, generated output, or an external contract.
- Use history and blame as navigation evidence, not proof that the most recent change caused the defect.

## Bisection safety

Use bisection only with a predicate that reliably distinguishes good from bad. Record the known-good and known-bad anchors and confirm them before starting. Account for build failures, schema incompatibility, dependency availability, generated files, and state that crosses revisions. Do not discard the user's working tree or switch revisions destructively; use safe repository-supported isolation when needed.

## No local reproduction

When CI or another inaccessible environment is the only failing surface:

- define the exact artifact, assertion, metric, trace, or failure signature being interpreted;
- compare environment and version evidence with the local state;
- distinguish observed CI behavior from locally inferred mechanisms;
- identify the next capture that would separate remaining hypotheses;
- never report `FIXED` until equivalent post-repair evidence exists.
