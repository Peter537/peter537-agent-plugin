# Focused application-security evidence

TODO-015 extends the existing audit suite, not its ownership or read-only authority. Follow the [behavior-first contract](../behavior-first-contract.md) and [verification map](../../docs/verification.md). No new skill, runner, discovery rule, or report schema is introduced.

## Coverage and interpretation

| Boundary | Evidence and control |
| --- | --- |
| Record ownership, tenancy, protected fields | `web-record-policy`: in-memory updates, owner rename, anonymous rejection; SQL policy remains inspected rather than executed. |
| Revoked privileges | `web-role-revocation`: repeat a privileged request with the same session after membership changes; preserve current-role cancellation and tenant checks. |
| Repeated state changes | `web-repeat-state-change`: a retry applies a second reservation; preserve scoped release receipts, payload checks and independent operations. |
| Shared state | `web-shared-state-isolation`: compare cold and warm private reads across owners and tenants; preserve scoped summaries and public reference data. |
| Upload bytes | `web-input-session-upload`: intercept the storage call before invoking the handler at 64 and 65 bytes. `web-upload-boundary-control` preserves actual upstream dispatch enforcement. |
| Equivalent and inapplicable controls | `web-managed-safe` preserves managed identity, application authorization and response minimization. `non-web-security-control` rejects irrelevant web requirements. |

The three new cases contain legitimate controls alongside defects. Existing independent false-positive cases remain indexed. Require actionable finding IDs, enforcement boundaries, minimum patch intent, preserved behavior, regression methods and evidence limits. Proposed fixes are neither authorized edits nor verified patches.

Characterization checks deliberately assert the observed defective behavior where present. Their success proves that observation, not that the security contract passes. Probes use small synthetic in-memory data, not live users, credentials, services, production storage, or a deployed database. Storage interception observes a call; it does not demonstrate a filesystem exploit. Scope replay guarantees to the explicit contract rather than imposing idempotency on every operation.

Method sources, reviewed 2026-09-30: [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) supports object-specific enforcement and negative tests; [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html#upload-and-download-limits) supports applicable byte limits. These motivate fixture boundaries, not universal architecture prescriptions or certification.

## Authorized personal-development procedure

Freeze the current packages, discovery metadata, prompts, expectations, fixture bytes and Git state, model/settings, capabilities and limits before trials. Materialize each selected seed once, then copy its complete bytes and Git state into external neutral workspaces. Add staged, unstaged, untracked, ignored and existing-runtime sentinels before freezing. Supply independent package copies; keep expectations and trial labels outside evaluated context.

Run the eight table cases once each against unchanged guidance, using sequential fresh subagents requested as `gpt-6-astra`/high. Each behavioral trial has 180 seconds; the complete model window, including one independent review, has 25 minutes. Maximum ten behavioral trials: a reproduced failure may justify one narrow correction in the security/reporting guidance and at most two additional trials for the affected case and nearest preservation control. Use identical frozen conditions for those comparisons. No blind retries, deadline extensions, native setup, or unsupported rewrites. Missing required evidence remains a completion gap.

For this TODO-015 run, fresh-agent capacity was exhausted after three completed trials. The user explicitly authorized reusing idle agents for the remaining five audits and independent review, with the original deadline unchanged. Keep workspaces and package copies separate, record prior context and reviewer independence, and do not describe these continuations as fresh-context trials. Retained context limits comparability; it does not authorize unsupported guidance corrections or a claim of uncontaminated repeated trials.

Capture actual responses and available action records, complete file bytes and Git state, package integrity, and parent replay results. Keep raw records local and temporary; report sanitized summaries. Distinguish direct observations from summarized actions and requested model settings from runtime attestation. No direct-subagent run proves native filesystem isolation or an exhaustive absence of intermediate actions.

One independent agent reviews neutral artifacts, findings, state comparisons and replay evidence without an author's proposed verdict. Record reviewer identity, requested settings, independence, consequential judgments and evidence references. Apply existing dimension verdicts and precedence; behavioral activation is not applicable. Cleanup is a separate required gate. This exception does not label agent review as human review or alter the comparison runner's human-review interface.

Keep discovery, invocation and routing byte-identical; routing trials are not needed here. Full suites, the canonical offline check, repeated matrices, broader controls/distribution checks and the unavailable bundled plugin validator remain deferred for this personal-development scope. Preserve release gates. Remove only verified owned fixtures, package copies, local raw records and processes after review.

## Focused commands

From the repository root:

```text
python -B evals/validate_eval_manifests.py
python -B evals/deep-code-audit/materialize_fixtures.py --list
python -B -m unittest discover -s evals/deep-code-audit/tests -p test_security_fixtures.py -v
```

Use repeated `--case <id>` arguments with `--output <empty-external-directory>` for the eight selected materializations. The preparation tests reuse the existing materializer and shared containment/state/cleanup helpers; they do not launch models or install tools. Run only reviewed fixture commands with `python -B`, and compare state afterward. Validate the skill package if guidance changes. Finish with resource/metadata review, the complete diff, `git diff --check`, final Git state and ownership-checked teardown.
