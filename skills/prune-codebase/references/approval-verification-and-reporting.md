# Approval, Verification, and Reporting

Use this reference for every broad candidate report and before applying any removal.

## Distinguish discovery from authorization

A broad request names a repository, subsystem, or cleanup category without identifying exact removal targets. It authorizes investigation and a read-only report, not deletion. Examples include "prune this repository," "clean up dead code," or "remove stale flags."

A precise removal or edit request names exact symbols, paths, flags, routes, migration identifiers, or candidate IDs. It authorizes only those targets, subject to re-verification and the ordinary safety boundary. A review remains read-only even when it names exact targets, and ambiguous wording defaults to review.

Candidate IDs are report-stable handles, not permanent repository identities. Assign sequential IDs such as `PC-001`, keep them attached when a candidate is narrowed, and never silently reuse an ID for a different surface. On a later task, verify that the repository revision and identifying locations still match before accepting prior approval.

## Present approval-ready candidates

For each candidate, report:

```markdown
### PC-001: [Consequence-oriented title]

- Classification: ready | needs-decision | keep | research-gated
- Risk: high | medium | low
- Confidence: high | medium | low
- Owning subsystem:
- Locations:
- Proposed coherent batch:
- Maintenance consequence:
- Liveness evidence:
- Lifecycle evidence:
- Entrypoints, variants, and consumers checked:
- Coverage gaps:
- Verification plan:
- Residual uncertainty:
```

Lead with `ready` candidates. Include `needs-decision` and `research-gated` candidates when the user's choice or more evidence can advance them. Keep `keep` entries only when they explain a likely false positive, preserve consequential complexity, or prevent repeated review churn.

Group candidates into approval batches by one reachability chain or retirement concept. Do not combine unrelated deletions merely because one command can remove them together. State prerequisites that remain outside this skill, such as dependency removal, external flag changes, data operations, compatibility decisions, or deployment.

## Re-verify before mutation

Immediately before editing:

1. Confirm the current revision and compare Git state with the review snapshot.
2. Resolve every approved ID to its original location and owning concept.
3. Repeat decision-critical reference, entrypoint, variant, dynamic-consumer, public-contract, and lifecycle checks.
4. Inspect new or changed tests, configuration, generated inputs, and downstream evidence.
5. Reclassify and stop for confirmation when scope, risk, or the coherent batch changed materially.

Do not interpret approval of one candidate as approval of newly exposed dead code. Report or seek approval for the new candidate unless it is an inseparable internal part of the exact approved reachability chain and was described in the batch.

## Preserve behavior and repository state

- Run the smallest trustworthy existing baseline checks before editing when feasible.
- Record pre-existing failures and do not mask them with retries, suppressions, skipped tests, broad fallbacks, or changed assertions.
- Remove registrations, tests, documentation, configuration, and assets only when their sole contract is the approved retired surface.
- Re-run the same checks plus checks for affected packaging, public contracts, variants, startup, shutdown, recovery, and generated outputs.
- Review the complete diff and final Git state. Remove task-created temporary artifacts and report every unexpected mutation.
- If a check requires installation, deployment, external mutation, destructive data work, or credentials beyond the request, leave it unrun and state the resulting confidence limit.

If the baseline is already failing, a safe removal may still proceed only when independent evidence distinguishes the known failure from the changed behavior. Otherwise return `BLOCKED` rather than declaring success.

## Report the outcome

For `REVIEWED`, include the scope and revision, classified candidates, coverage, checks, gaps, final unchanged repository state, and the exact IDs ready for approval.

For `PRUNED`, include:

- approved IDs and the coherent batch actually removed;
- decisive liveness and lifecycle evidence rechecked before editing;
- changed files and any intentionally removed tests, registrations, configuration, documentation, or assets;
- baseline and after checks, packaging or variant coverage, and failures;
- initial-to-final Git-state comparison;
- newly discovered candidates that were not changed;
- unrun checks and residual uncertainty.

Use `NO_CHANGE` when an authorized prune request ends without removal because re-verification preserves the target or no approved candidate survives. A completed read-only review returns `REVIEWED`, including a verified no-candidate result. Use `BLOCKED` when missing evidence or authority prevents a trustworthy conclusion. Do not equate fewer lines, files, warnings, or dependencies with success; the outcome is safe removal of an evidenced obsolete contract.

## Primary references

Accessed 2026-08-20.

- [Git grep](https://git-scm.com/docs/git-grep) documents revision-aware repository searching used as supporting, not conclusive, evidence.
- [Git diff](https://git-scm.com/docs/git-diff) and [Git status](https://git-scm.com/docs/git-status) provide the authoritative local change boundary for pre/post comparison.
- [Semantic Versioning 2.0.0](https://semver.org/) describes compatibility signaling when pruning affects a versioned public API.
