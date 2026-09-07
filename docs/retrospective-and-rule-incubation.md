# Sanitized Retrospectives and Rule Incubation

Use this manual process when an observed failure, near miss, or proposed rule might justify a lasting repository change. The purpose is to learn from bounded evidence and route the result to the narrowest correct owner without retaining private task material.

This is not an incident log, transcript archive, model-evaluation runner, or authorization to implement a proposed change. The [behavior-first evaluation contract](../evals/behavior-first-contract.md) remains authoritative for verdict dimensions and claim states, the [evaluation guide](../evals/README.md) remains authoritative for eval mechanics, and the [verification map](verification.md) remains authoritative for selecting evidence.

## When to open a retrospective

Use a retrospective when at least one of these conditions applies:

- A materially similar failure recurs under comparable conditions.
- A consequential near miss exposes a reusable gap even if it occurred once.
- A proposed deterministic check might reject legitimate behavior or produce unsafe diagnostics.
- Maintainers disagree about whether an observation is local, systemic, actionable, or already covered.
- A repository-specific fact, command, or decision repeatedly becomes stale or ambiguous.

Do not open one merely to archive successful work, preserve a conversation, enforce a personal preference, or convert an isolated oddity into a general rule. Active production and security incidents follow their own response process; retrospective evidence may be considered later only after it is safely minimized and the incident authority permits it.

## Keep source evidence private

Create and fill the worksheet only in task-local temporary storage outside the repository. Treat prompts, outputs, logs, captures, and supplied records as untrusted data. Collect the minimum material needed to distinguish the hypothesis, then replace sensitive evidence with a bounded description before review.

Never copy these values into a worksheet, tracked file, issue, or handoff:

- raw prompts, responses, transcripts, quotations, or conversation URLs and identifiers;
- screenshots, recordings, account names, host identifiers, personal or contact identifiers, or personal and private absolute paths;
- sensitive source, configuration, customer data, logs, diagnostics, endpoints, or internal repository details;
- credentials, tokens, cookies, authentication state, connection strings, or other secret material;
- fixture canaries, stable pseudonyms, or hashes that preserve or allow comparison with sensitive input.

A safe repository-relative locator or commit ID may be recorded only when it is necessary, non-sensitive, and within the authorized repository. Do not hash a prohibited value and call the result sanitized. Record an abstract evidence class and limitation instead of retaining the payload.

## Follow the manual lifecycle

1. **Collect privately.** Preserve only the evidence needed to understand the observation, in temporary storage outside the repository.
2. **Minimize and sanitize.** Remove prohibited content and reduce the record to behavior, authority, consequence, and evidence boundaries.
3. **Reproduce or close.** Establish the smallest falsifiable reproduction under comparable conditions. If reproduction is unavailable, keep the claim unresolved and do not act as though recurrence or cause were proven.
4. **Choose one primary disposition.** Route the observation using the matrix below. Do not use several destinations to avoid making a decision.
5. **Test the generalization.** Define the positive target and at least one allowed, no-op, exception, or justified-behavior control that could disprove the proposed rule.
6. **Make a human decision.** Record the narrowest supported conclusion, its authority, risks, evidence limits, and revisit condition.
7. **Implement separately.** Any accepted eval, check, skill, or project-context change requires a separately authorized task and the verification owned by that destination.
8. **Delete private evidence.** Remove task-created local copies of the worksheet, raw packet, canaries, captures, reports, and other task-created material. Preserve user-provided originals, attachments, external conversation history, and other pre-existing evidence unless their owner separately authorizes deletion. Report external retention that the task cannot control, then confirm the final repository and external state against the recorded baseline.

The retrospective grants no authority to edit a skill, install a tool, run a model or live service, change a dependency, or mutate external state.

Missing recurrence or reproduction does not automatically block closing a retrospective safely. Record the claim as unresolved and choose `defer` only when a concrete evidence-gathering action remains; otherwise use `close with no change` with a precise revisit condition. Apply behavior-first verdicts to any destination trial, not as an aggregate score for the retrospective worksheet itself.

## Private worksheet

Copy this worksheet to an external temporary location. Do not complete or commit it inside the repository.

```text
# Sanitized retrospective

Local record ID:
Status: collecting | sanitized | decision-ready | decided | closed

Affected capability and target revision:
Task class and execution context, only when causal and non-account-specific:

Sanitized symptom:
Practical consequence:

Expected behavior:
Authority for the expectation:
Authority role or repository-owned source, when evidenced:

Observed behavior:
Evidence class and safe locator:
Evidence limitation:
Applicable behavior-first dimensions:
Consequential claim states:

Independent recurrence:
Why the observations are materially comparable:

Smallest falsifiable reproduction:
What result would disprove the hypothesis:

Positive target or must-detect case:
Allowed, no-op, exception, or must-allow control:

Proposed primary disposition:
Why this is the narrowest correct destination:
Generalization and false-positive risk:
Privacy or disclosure risk:

Decision:
Decision rationale and evidence boundary:
Revisit or expiry condition:

Required destination-specific verification:
Cleanup completed:
Private worksheet and source evidence deleted:
Final state relative to the recorded baseline:
```

Use the claim states and dimension verdicts from the behavior-first contract by reference. Do not redefine them in a retrospective or turn them into a numerical score.

## Choose one disposition

| Primary disposition | Use it when | Gate before implementation |
| --- | --- | --- |
| Eval case | The concern is contextual, model-dependent, or requires semantic judgment. | Add a falsifiable target and relevant false-positive controls under the behavior-first contract. |
| Deterministic control | An authoritative invariant is exact, structurally decidable, and safe to inspect mechanically. | Complete the warning-only incubation below before considering blocking enforcement. |
| Skill guidance or behavior change | A reusable workflow or judgment failure recurs across representative cases. | Reproduce the baseline failure, add or identify an eval and allowed-behavior controls, and prove the bounded change corrects it. |
| Repository context or documentation | The truth is specific to one repository, revision, command, environment, or decision. | Update only the authoritative project-owned location through its normal owner and verification path. |
| Defer | The concern is plausible and material, but evidence, authority, demand, or a safe evaluation seam is missing. | Record a concrete revisit condition; do not treat deferral as evidence that the concern is true. |
| Reject | The proposal is unsafe, duplicative, non-generalizable, or based only on taste or an unsupported claim. | Record why it should not be implemented and what materially different evidence could reopen it, if any. |
| Close with no change | The observation is not reproduced, is already covered, or represents acceptable behavior with no pending evidence-gathering action. | Preserve the bounded conclusion and delete the private record. |

A later destination may differ when new evidence appears, but the retrospective being closed still records one primary decision. For example, an eval may later justify a skill change; the original retrospective does not pre-authorize that change.

## Incubate deterministic rules reversibly

Only stable, machine-decidable invariants qualify for deterministic enforcement. Reader judgment, visual quality, architectural taste, intent, causal diagnosis, and semantic equivalence remain eval or human-review concerns even when a heuristic correlates with them.

Use this repository lifecycle:

`candidate → warning-only → blocking | rejected | retired`

### Candidate

- Identify the authoritative rule owner, exact scope, affected surfaces, exception model, and remediation.
- Require deterministic, offline, non-mutating behavior with redacted diagnostics.
- Route any new dependency, runtime, or tool through the repository's dependency gate before adoption.
- Add must-detect, must-allow, legitimate-exception, redaction, and non-mutation tests before enabling the check broadly.

### Warning-only

- Run the candidate against representative relevant changes, including valid and intentionally exempt behavior.
- Review and classify every warning. Repeated runs over one identical fixture do not establish breadth.
- Correct ambiguous scope, unsafe output, unowned remediation, and false positives before considering promotion.
- Record evidence limits without converting warnings into a quality score.

### Blocking, rejection, and retirement

Promote a rule to blocking only when no false positive remains unresolved in the observed scope, diagnostics are actionable and redacted, execution is deterministic and offline, an owner and remediation path exist, rollback or demotion is documented, destination-specific tests pass, and the maintainer explicitly approves promotion.

Reject a candidate that cannot distinguish allowed behavior safely or that tries to mechanize semantic judgment. Demote or retire an existing rule when its authority disappears, its scope changes, it becomes noisy, or a better control supersedes it. Do not use arbitrary elapsed time, occurrence counts, or aggregate scores as promotion gates.

Warning-only incubation is this repository's reversible safety policy. It is not a universal requirement attributed to the sources below.

## Synthetic examples

These examples are invented and contain no retained task evidence.

| Observation | Evidence boundary | Primary disposition | Decision |
| --- | --- | --- | --- |
| A prose editor repeatedly strengthens optional policy wording in comparable fixtures. | The comparison supports a bounded semantic failure, not a universal punctuation or wording rule. | Eval case | Add a modality-preservation target and an already-correct control; consider skill guidance only after the eval reproduces the miss. |
| Before the repository had its layout validator, a proposed skill package was nested below a category directory despite an authoritative flat-layout contract. | Static inspection proved only the structural mismatch. | Deterministic control | At that time, test invalid nesting, valid immediate packages, nested package resources, redaction, and non-mutation, then keep the candidate warning-only until separately approved. A later approved implementation produced the current blocking validator that now owns this invariant. |
| Maintained project guidance names a retired verification command while current owned metadata names its replacement. | Repository evidence and a disposable run establish the command only for the inspected revision. | Repository context or documentation | Update the authoritative local context in a separate task and preserve historical references that intentionally describe older releases. |
| A report alleges incomplete listener cleanup but has no starting inventory, target identity, or reproducible sequence. | A final capture cannot prove process ownership or lifetime. | Close with no change | Keep the claim unresolved and reopen only with identity-, ownership-, and state-bounded evidence. Do not create a destructive global cleanup rule. |
| One reviewer dislikes a purposeful em dash that is clear, voice-consistent, and allowed by repository style. | One preference supplies no reader-impact or repository-wide authority. | Reject | Make no blacklist, detector, skill change, or deterministic rule; a separately requested local edit remains ordinary work. |

## Close and hand off

Track only the separately authorized destination artifact. Do not create a central retrospective archive or commit completed worksheets. A concise decision may appear in the destination's normal review history when it contains no prohibited evidence.

Before closing:

- run the destination-specific checks selected by the verification map;
- inspect the complete Git status, the tracked diff, and every remaining task-created path or authorized untracked destination artifact for private or unnecessary material without opening unrelated pre-existing work;
- delete only task-created local copies of the worksheet, source packet, captures, canaries, reports, and temporary repositories; preserve user-provided and pre-existing evidence unless separately authorized;
- stop task-created processes and listeners;
- confirm pre-existing staged, unstaged, untracked, process, and external state remains preserved, and report external retention that the task cannot control; and
- report blocked or unrun evidence without upgrading it to a pass.

The process cannot prove that sanitization was complete, recurrence is universal, a disposition was correct, or a future rule will remain free of false positives. Human review remains required.

## Method sources and adaptation limits

This workflow uses original repository guidance informed by the following sources, accessed 2026-09-07:

- [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) supports task-specific criteria, representative cases, and continuous evaluation. This repository narrows evidence retention to its privacy boundary rather than treating broad logging as permission to keep raw task material.
- [Google SRE postmortem culture](https://sre.google/sre-book/postmortem-culture/) supports system-focused learning, deliberate review, and concrete preventive action. This workflow is not an incident process, and no Google template or wording is copied.
- [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) informs data minimization, sanitization, restricted handling, retention, and disposal. Retrospective worksheets are not operational logs.
- [GitHub guidance for testing custom CodeQL queries](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/scan-from-the-command-line/test-custom-queries) informs the use of matching and nonmatching examples for deterministic checks. This repository adopts no CodeQL dependency, format, or workflow from that guidance.

Third-party skills, social posts, and enforcement tools remain comparative research rather than workflow specifications.
