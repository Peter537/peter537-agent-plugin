# Opt-in behavioral comparisons

Use `run_comparisons.py` to freeze inputs, run explicitly authorized behavioral trials, assess their evidence, and remove the disposable bundle. The records follow the [behavior-first contract](behavior-first-contract.md). They are independent of a provider's evaluation API; the first execution adapter targets the installed Codex CLI.

The workflow has offline regression coverage and bounded native execution evidence on Windows with Codex CLI `0.158.0-alpha.2.1` and `gpt-6-astra` at high reasoning. This establishes compatibility for the exercised configuration, not every host or a skill-quality improvement. A compatible version must expose the native configuration, skill, and instruction inventories required by preflight. Missing capabilities block execution; the runner never installs or upgrades Codex.

## Prepare a comparison

Create the specification outside this repository. Supply absolute local paths for the candidate skill package and any prepared seeds. Select behavioral case IDs from one existing suite. Routing and live-case execution are unsupported: retain the manual full-catalog routing procedure and separately authorized live workflows.

This specification illustrates three documentation cases. Replace the candidate path and review the execution settings before preparing it. An empty `ambientSkills` list declares that no other skills may be enabled; populate it with the complete intended native inventory when that is not true. No model runs during preparation.

```json
{
  "schemaVersion": 1,
  "suite": "docs-audit",
  "candidatePackage": "/absolute/path/to/candidate/docs-audit",
  "authorization": "Compare documentation behavior in these disposable fixtures only.",
  "settings": {
    "executable": "codex",
    "model": "gpt-6-astra",
    "reasoningEffort": "high",
    "sandbox": "workspace-write",
    "approvalPolicy": "never",
    "ambientSkills": [],
    "config": {},
    "contextManagement": {}
  },
  "limits": {
    "maxTrials": 9,
    "trialTimeoutSeconds": 600,
    "batchTimeoutSeconds": 5400
  },
  "cases": [
    {
      "id": "stale-public-contract",
      "heldOut": false,
      "setup": {"kind": "materializer", "reviewed": true},
      "allowedPaths": ["README.md"],
      "promptOverride": {
        "text": "Update this repository's public documentation to match the implemented service contract.",
        "reason": "Use the same task-only request in all three variants."
      }
    },
    {
      "id": "accurate-no-op",
      "heldOut": false,
      "setup": {"kind": "materializer", "reviewed": true},
      "allowedPaths": ["README.md"],
      "promptOverride": {
        "text": "Refresh the repository documentation. Make no changes that are not supported by implementation evidence.",
        "reason": "Use the same task-only request in all three variants."
      }
    },
    {
      "id": "plain-audit-stale-public-contract",
      "heldOut": true,
      "setup": {"kind": "materializer", "reviewed": true},
      "allowedPaths": [],
      "promptOverride": {
        "text": "Audit this repository's documentation against the implemented service contract.",
        "reason": "Use the same task-only request in all three variants."
      }
    }
  ]
}
```

The authorization text records the scope; it does not grant permission by itself. Model execution still requires the user's task-specific authorization. The three-case example checks infrastructure and does not replace the applicable positive cases and indexed false-positive controls required when changing a skill.

Run from the source checkout:

```text
python -B evals/run_comparisons.py prepare --spec <external-spec.json> --output <empty-external-run-directory>
```

Keep the returned cleanup token outside the bundle. A new or empty directory must be outside the source checkout, candidate package, and supplied seeds. Links, junctions, traversal, and overlapping paths are rejected. Preparation failures leave owned partial output for inspection and explicit cleanup.

The native sandbox must also be able to traverse the directory's parents. On Windows, an owner-only temporary parent can block fixture access even when native inventory succeeds. Use a task-owned directory with appropriate inherited permissions; do not weaken the sandbox or change global permissions. For a new storage location, an installed-version [model-free sandbox command](https://learn.chatgpt.com/docs/developer-commands) can check access before spending model calls. Preparation alone does not establish sandbox access.

Preparation freezes the specification, current and candidate packages, manifest expectations, source state, held-out selection, and fixture seeds. Existing materializers run once per selected case; their case-ID child directory becomes the seed. Every repetition and variant receives the same complete seed bytes and Git state. For `write-clearly` or other unsupported setup, supply `{"kind":"seed","reviewed":true,"path":"/absolute/prepared/repository"}` instead. The supplied directory itself is the working directory. Setup prose is never executed.

The optional positive integer `repetitions` defaults to one. `maxTrials` must cover every selected case, repetition, and variant. At least one case must be designated held out before execution. Once held-out results inform a revision, do not present those same cases as untouched evidence for that revision.

`allowedPaths` names exact relative files. A trailing `/` explicitly permits a directory's descendants. Empty paths, wildcards, traversal, and Git/skill-overlay ownership changes are unsupported. This list is a deterministic ceiling, not expanded task authority: a no-op case can still fail semantic review for an unnecessary edit inside its authorized README.

`promptOverride` is required when the manifest prompt explicitly names a skill. Author and review its text and reason before observing results. Use it identically across variants; the original prompt and unchanged expectations remain in the frozen record. Interpret skill-specific mechanisms separately from the underlying task outcome. Never relax expectations after observing a no-skill failure.

## Execution boundary

Only this operation can initiate model execution:

```text
python -B evals/run_comparisons.py run --run-dir <external-run-directory> --allow-model-execution
```

The CLI has no simulated execution flag. Tests inject a fake adapter through the Python interface. The canonical offline runner sets an additional guard that rejects the native adapter even if a test accidentally requests it.

“No-skill” means without the evaluated package and its discovery entry, not an entirely skill-free host. Other declared ambient skills and instructions stay fixed. Each `ambientSkills` entry contains an absolute package `path`, its `name`, and a `sha256` produced by `comparison_codex.package_fingerprint`. It hashes canonical ordered relative-file/content-digest pairs; it is not the hash of `SKILL.md` alone.

Current and candidate trials add a frozen local package copy at `.agents/skills/<suite>` inside the disposable working directory. This harness overlay permits actual native discovery within the repository boundary. Its presence is the intended treatment; the underlying seed remains identical. Seeds that already occupy that location are rejected. The overlay is included in integrity checks and cannot be changed through `allowedPaths`; it is checked for mutation rather than made physically unwritable. This is a local-skill comparison, not evidence of marketplace installation or plugin discovery.

The adapter inventories effective configuration, requirements, available skills, and loaded instruction sources through model-free native preflight. It disables duplicate copies of the evaluated package using process-local configuration overrides, verifies the selected package and complete declared ambient inventory, and compares environment identities across variants. Process-local trust for the exact disposable workspace prevents native thread initialization from persisting a project-trust entry; an explicitly untrusted workspace or ancestor blocks execution. The adapter checks the user's configuration bytes around native operations and stops the batch if they change. It never restores that file automatically or treats `--ignore-user-config` as an isolation guarantee. Changed effective settings or unavailable inventory block execution.

Use `config` and `contextManagement` for explicit supported dotted configuration overrides. The dedicated model, reasoning, sandbox, approval, and skill-enablement fields cannot be overridden through those maps. Keep tool capabilities, context settings, ambient authority, and permissions equivalent. The initial adapter supports local execution with native sandboxing and denied approval escalation. Its fixed process-local settings disable hooks, apps, plugins, memories, subagents, web search, browser and computer use, image generation, skill dependency installation, and command networking; enabled MCP configuration also blocks startup. Effective settings must confirm those restrictions. Cases requiring those capabilities need a different, separately reviewed execution path. The adapter preserves inherited command rules and managed restrictions.

Trials run sequentially. The runner enforces maximum attempted trials, a per-trial deadline covering preflight and checks, and a wall-clock batch deadline starting at the first run invocation. Reinvoking `run` verifies frozen inputs and skips attempted trials; it never retries them automatically or resets the budget. An interrupted running record requires investigation rather than blind continuation. To retry an experiment, prepare a separately authorized new bundle.

A state-preservation failure or unconfirmed teardown stops the batch. Unstarted trials remain `NOT_RUN`; resuming cannot bypass that failure. Inspect the retained evidence and resolve any shared-state or cleanup issue before preparing independent work in a fresh bundle. Do not change an attempted trial's scope or ledger to make the comparison continue.

An optional case `verification` array declares reviewed repository-native checks, each with `phase` (`before` or `after`), direct `argv`, `reason`, `timeoutSeconds`, and `expectedExitCodes`. Supported executable names are `python`, `python3`, `py`, and `dotnet`. For example, a Python check can use `["python","-B","-m","unittest","discover","-s","tests","-v"]`. Nonzero expected exits can represent an authentic failing baseline. Review commands and their cleanup before selecting them: structural validation is not a safety proof. The runner never automatically executes manifest `verificationCommands`.

The native adapter and selected local checks own and tear down their process trees. A timeout blocks completion evidence even when teardown succeeds; unconfirmed teardown also blocks cleanup. Do not select a command that starts a persistent service. Cleanup never kills a PID merely because editable evidence names it.

## Review and compare

Process completion and assessment are separate. Execution records retain actual events, responses, private before/after copies, file identities, staged contents, Git state, command results, cleanup status, and measured telemetry. Raw Git index hashes are diagnostic; a stat-cache refresh alone is not a staged-content change. Ignored and untracked files remain visible to integrity checks. Snapshotting rejects Git includes and executable clean, smudge, or process filters before worktree inspection; these configurations need a separately reviewed snapshot path.

Create an external review JSON object with `schemaVersion: 1` and a `reviews` array. Each review contains:

- `trialId`, matching the neutral identifier in the frozen comparison.
- `reviewer`, with `kind: "human"` and a nonempty local reviewer identifier. Simulated executions require `kind: "simulated"` and cannot substitute for human review of model evidence.
- `dimensions`, containing `activation`, `outcome`, `evidence`, `authorization`, `scope`, and `state`. Each has a `verdict`, a nonempty `reason`, and an `evidence` array of file paths relative to that trial's evidence directory. Passing and failing decisions require evidence. Behavioral activation is always `NOT_APPLICABLE`.
- `claims`, an array of consequential conclusions with `text`, `state`, and `evidence`. Claim states are `supported`, `bounded`, `unresolved`, and `unsupported`. Supported and bounded claims require evidence; unsupported claims fail claim-to-evidence assessment.
- `contaminated`, a boolean recording exposure to grading expectations, comparison labels, or other invalidating context. Contamination invalidates comparison evidence.

Optional `annotations` record reviewed overhead observations. Each has `metric` (`observedReads`, `repeatedChecks`, or `approvalEvents`), a nonnegative integer `value`, `reason`, and nonempty `evidence`. These annotations remain distinguishable from adapter telemetry. A command containing a filename does not establish that the file was read, and repeated command strings do not prove unnecessary repeated checks.

Keep expectations, variant labels, review files, and raw trial records outside the agent's supplied context and workspace. Native sandboxing and the harness layout do not create a universal read-isolation boundary. Inspect traces for contamination and record it explicitly; absence of a recorded access is not universal proof that no access occurred.

```text
python -B evals/run_comparisons.py report --run-dir <external-run-directory> --reviews <external-reviews.json>
```

Without reviews, required semantic dimensions remain blocked. Deterministic state violations cannot be overridden by a passing review. Finalized record digests detect accidental record changes, and assessment recomputes state invariants. These local digests are not a cryptographic isolation boundary. Evidence or workspace drift invalidates the recorded comparison. An applicable failure takes precedence over a block; an unstarted trial stays `NOT_RUN`. Review files cannot turn an unstarted trial into a pass.

Reports expose safe case/trial identifiers, dimension verdicts, per-variant outcomes, dimension changes, and individual measurements. They do not print raw responses, reviewer prose, paths, or captured child output. Token usage comes only from telemetry. Reads, approval counts, cost, or other unavailable measurements remain unavailable rather than zero. No aggregate quality score, cost saving, latency improvement, or installed-host conclusion is inferred from shorter source text or simulated results.

## Cleanup and maintenance checks

Review evidence before deleting it, then run:

```text
python -B evals/run_comparisons.py cleanup --run-dir <external-run-directory> --token <saved-cleanup-token>
```

Cleanup checks ownership, containment, links, and recorded process teardown. It refuses an active or unconfirmed process state. Ownership markers protect against accidental deletion; they are not a cryptographic authorization mechanism. The caller must preserve the token outside agent-controlled files. Resolve blocked teardown using observed process ownership before removing the bundle.

Frozen inputs support replay while the external bundle exists. Deleting it ends exact replay; generating new randomized fixtures starts a new experiment. Preserve a concise sanitized disposition separately from raw evidence when authorized. Do not copy account output, canaries, transcripts, or captures into repository documentation.

Run the focused tests and canonical offline checks from the repository root:

```text
python -B -m unittest evals/test_comparison_workflow.py evals/test_comparison_state.py evals/test_comparison_codex.py -v
python -B evals/run_offline_checks.py
```

The offline command discovers these maintenance tests without invoking the comparison CLI. Fake transports, synthetic verdicts, and launch canaries establish the workflow's deterministic boundaries; they do not establish model behavior or live protocol compatibility. Exit `2` reports unavailable inputs, authority, evidence, or infrastructure; report exit `1` means a failing assessment, and report exit `0` requires every selected trial to pass its applicable dimensions.

## Native validation record

On 2026-09-28, authorized Windows trials exercised Codex CLI `0.158.0-alpha.2.1`, `gpt-6-astra`, high reasoning, workspace-write sandboxing, denied approval escalation, and identical current/candidate packages. Native inventories confirmed the evaluated package's absence or selected local copy, unchanged ambient skills, and matching effective configuration across each comparison's three variants.

- Three documentation-update trials corrected the stale README facts and preserved other state.
- The following no-skill no-op trial expanded an already-correct README. The runner recorded a state `FAIL`, stopped, and left five trials `NOT_RUN`. It refused a later attempt to resume that stopped bundle. The failure remains evidence of the guard working, not a passing no-op outcome.
- A fresh audit-only comparison completed all three variants: each reported the stale facts without edits. Its six reviewed fixture checks passed; together with the preceding four trials, 14 before/after fixture checks passed. Resuming the completed audit bundle changed no records and dispatched no additional trials.

An earlier nine-trial batch could not access its owner-only temporary parent; its processes completed, but assessments remained `BLOCKED`. It was excluded from successful task-execution evidence. Native investigation also exposed nullable configuration fields and persistent project-trust writes; the adapter now handles the former and uses verified process-local trust plus configuration-byte guards for the latter. The original user configuration was restored exactly after the initial probe and remained unchanged in subsequent execution.

Reporting retained actual event/token telemetry and elapsed time, while unavailable measurements stayed unavailable. No human semantic review records were supplied: otherwise completed trials therefore remained `BLOCKED` for assessment. This verifies exercised infrastructure paths and a real failure guard, not an all-passing nine-trial comparison, a skill improvement, universal filesystem isolation, or installed-plugin behavior. Raw evidence is disposable; the retained record is this bounded summary.

## Sources

The trace-based adapter design follows [OpenAI's skill-evaluation guidance](https://developers.openai.com/blog/eval-skills). Native inventories and process-local enablement use the documented [app-server interface](https://learn.chatgpt.com/docs/app-server) and [skill configuration](https://learn.chatgpt.com/docs/build-skills), checked during planning on 2026-09-28. These sources motivate the interface; installed-version compatibility remains a separate execution check.
