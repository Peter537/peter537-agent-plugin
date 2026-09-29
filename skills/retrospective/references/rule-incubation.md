# Reversible deterministic-rule incubation

Load when the proposed disposition involves a deterministic rule, including an existing warning or a request for promotion, demotion, rejection, or retirement. The retrospective recommends a disposition; implementing or running a new check still requires its own authority.

Only exact, authoritative, machine-decidable invariants qualify. Reader judgment, visual quality, architectural taste, intent, causal explanation, and semantic equivalence do not become deterministic merely because a heuristic correlates with them.

The portable default is:

`candidate → warning-only → blocking | rejected | retired`

Follow applicable project policy, including stronger execution or review gates. This lifecycle is the plugin's reversible safety policy, not an external standard or permission to bypass an existing decision owner.

## Candidate

Identify the rule owner, exact scope, affected surfaces, exceptions, remediation, and rollback. Require offline, deterministic, non-mutating operation and redacted diagnostics. Define must-detect, must-allow, legitimate-exception, redaction, and state-preservation tests. Any new dependency, runtime, or tool follows the project's dependency and execution authority before adoption.

## Warning-only

Evaluate representative relevant changes, including permitted and intentionally exempt behavior. Classify every warning and resolve unsafe output, ambiguous scope, false positives, or unowned remediation. Repeated runs over one unchanged fixture do not establish coverage across different situations. Describe the evidence limits without inventing a quality score.

## Promotion, rejection, and retirement

Blocking promotion requires all of these: no unresolved false positive in the observed scope; actionable redacted diagnostics; deterministic offline behavior; an owner and remediation path; documented rollback or demotion; passing destination-specific checks; and explicit maintainer approval. A prior approval covers only its stated scope and conditions.

Reject a rule that cannot distinguish permitted behavior safely or attempts to enforce semantic judgment mechanically. Demote or retire it when its authority disappears, its scope changes, it becomes noisy, or better protection supersedes it. A broad filename rule that rejects maintained compatibility adapters is not rescued by deleting those adapters or suppressing the exception evidence.

Do not use a fixed age, occurrence count, deletion quota, or aggregate score as a promotion gate. Supply the required evidence and recommendation to the human owner; do not enable enforcement from the retrospective.

The use of matching and nonmatching examples is informed by [GitHub's query-testing guidance](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/scan-from-the-command-line/test-custom-queries), checked 2026-09-29. No CodeQL dependency, template, or workflow is adopted.
