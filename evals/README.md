# Skill Evaluations

This directory contains repository-maintenance evaluations for the skills distributed by Peter537 Agent Plugin. The evaluation assets are not installed with an individual skill and are not runtime dependencies of the plugin.

Use the [behavior-first evaluation contract](behavior-first-contract.md) to design and grade cases, and use the [repository verification map](../docs/verification.md) to select the complete evidence required for a changed surface. This file remains the authority for eval-specific commands and safety constraints.

## Canonical offline check

Run the dependency-free repository baseline from the repository root:

```text
python -B evals/run_offline_checks.py
python -B evals/run_offline_checks.py --root <repository>
```

The command discovers tracked and nonignored untracked repository files, performs bounded JSON, YAML/frontmatter, Python, and local Markdown-link checks, runs development-mode layout and common eval-manifest validation, invokes each suite's single materializer `--list` interface, and runs root maintenance tests plus distributed-script test suites. Discovery and execution order are deterministic. Generic static inspection excludes `.git`, intentionally malformed `evals/<slug>/fixtures/**` payloads, and nontracked cache or build outputs; tracked repository-owned files remain checked even when their directory has a build-like name.

Exit `0` means every required offline check passed and the Git-visible repository state and path inventory remained unchanged. Exit `1` means at least one completed validation or test failed, or repository mutation was detected. Exit `2` means an infrastructure failure prevented reliable completion, including unsafe root discovery, filesystem inspection failure, unavailable writable temporary storage, child-process launch failure, or timeout. Independent failures are aggregated where their discovery remains trustworthy.

The runner uses fixed direct Python argument arrays, closed standard input, captured child output, deterministic environment settings, and a fixed timeout. It dispatches only the Git-visible validators, materializer `--list` entry points, and test modules defined by this maintenance contract. Reviewed maintenance tests may materialize and exercise disposable local fixtures; manifest presence never authorizes command execution. The runner does not initiate model trials, live cases, dependency installation, or services. Diagnostics identify checks and repository-relative locations without reproducing child output, matched values, canaries, private paths, or source snippets.

The runner is an orchestrator, not an operating-system sandbox. Its reviewed child entry points are required to remain offline and nonpersistent, but the runner cannot technically prevent a changed child script from using the network or spawning descendants, and a timeout bounds only the direct child process. Captured child output is suppressed from diagnostics but is not itself proof that the child was safe.

Run its standard-library tests with:

```text
python -B -m unittest evals/test_offline_checks.py -v
```

Python 3, local Git, and writable operating-system temporary storage are prerequisites. The command deliberately does not run strict release grouping, bundled skill or plugin validators, external schemas, model comparisons, live or runtime checks, MCP connections, installation, tagging, submission, or publication. Its final informational `NOT_RUN` boundary points to the [repository verification map](../docs/verification.md) for that evidence. A successful run proves only the bounded offline contracts it reports.

## Suite contract

Each of the sixteen suites uses a versioned `cases.json` manifest with task-specific required signals, prohibited behavior, false-positive controls, trigger cases, and repository-state invariants. Repository-oriented suites also provide compact fixture templates and a standard-library `materialize_fixtures.py` command. The [behavior-first evaluation contract](behavior-first-contract.md) is the canonical, platform-neutral grading policy across all suites.

The evaluation tree intentionally mirrors the flat plugin layout: every immediate `skills/<slug>/` package has one immediate `evals/<slug>/cases.json` suite. Category directories must not be introduced under either tree because Agent Plugin skill discovery requires each package to be an immediate child of `skills/`. Human-facing categories live in `docs/skills/README.md`, while `skills.sh.json` is the machine-readable grouping source.

## Common manifest validation

Run the read-only, standard-library validator from the repository root:

```text
python -B evals/validate_eval_manifests.py
python -B evals/validate_eval_manifests.py --root <repository>
```

Exit `0` means every discovered manifest, the cross-skill routing matrix, and the handoff scenario index satisfy their structural contracts. Exit `1` means parsed metadata contains validation errors. Exit `2` means root discovery, file reading, or JSON parsing failed. Diagnostics are deterministic and repository-relative; privacy findings identify only the field location, never the offending value.

The shared contract requires `schemaVersion: 1`, `suiteExpectations`, nonempty `cases`, and nonempty `triggerCases`. The only optional top-level fields are `suite` and `liveCases`; when present, `suite` must match its directory. `suiteExpectations.falsePositiveControls` is a nonempty, unique list of IDs that resolve only to behavioral cases in the same suite.

Behavioral cases require lowercase slug IDs, descriptions, prompts, fixtures, and an `expected` object with nonempty `requiredSignals`, `prohibitedSignals`, and `repositoryState`; `expected.outcome` remains optional. Case-level suite metadata remains open, but `expected` accepts no other fields and behavioral cases cannot contain routing expectations. Trigger cases contain only an ID, prompt, boolean `expectActivation`, and one canonical `expectedOwner`; execution expectations do not belong in triggers. IDs must be unique across behavioral, trigger, and live cases within one suite, while different suites may reuse an ID.

Signal comparison collapses whitespace and applies Unicode case folding. Normalized duplicates within a list and direct overlap between required and prohibited signals are invalid. Diagnostics identify the field location without printing the signal value. The validator also preserves its read-only boundary and rejects hidden golden-response fields inside `expected`.

Every suite must include at least one behavioral case, one positive trigger, and one negative trigger. The common contract imposes no arbitrary suite-size threshold; scenario-specific repetition remains valid when the behavior itself requires it. This contract follows [OpenAI's evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices) by requiring task-specific structured evidence without reducing quality to a numerical score. OpenAI is deprecating its legacy Evals platform, so this repository's contract does not depend on that API. See the separate [submission guidance](https://developers.openai.com/plugins/deploy/submission) for public-submission requirements.

Fixture references, including aliases, must resolve beneath the suite's `fixtures/` directory without traversal, `.git`, symlinks, junctions, or reparse points. Known path-bearing metadata must be repository-relative, although generated targets need not exist. Every manifest string is checked for Windows or Unix personal-home absolute paths. Skill owners use bare discovered slugs; `$slug` is reserved for explicit invocation inside prompts. Non-skill owners must be declared in [`routing-matrix.json`](routing-matrix.json), including `no-skill` for requests that no skill in this plugin owns. Positive triggers must name their suite, while negative triggers must name another skill or a registered non-skill owner.

## Cross-skill routing matrix

[`routing-matrix.json`](routing-matrix.json) indexes the prompts owned by the sixteen suite manifests instead of copying them. It declares the non-skill owner vocabulary, pairs one explicit and one natural-language invocation case for every skill, records each material reciprocal boundary once, and points to behavioral coverage for specialist handoffs, progressive disclosure, and full-catalog collisions.

The common validator derives effective implicit-invocation policy from `skills/<slug>/agents/openai.yaml`; omission means the documented default `true`. Each explicit case must contain the exact `$slug` token and activate its skill. A natural-language case must contain no explicit skill mention and must follow that skill's effective policy. Boundary rows contain two sorted skill slugs and both negative routing directions, with every referenced trigger owned by the opposite skill.

`verification-context` sets `allow_implicit_invocation: false`. Its routing evaluation must therefore activate only on explicit `$verification-context` invocation and keep an otherwise matching natural-language request inactive. Its behavioral evaluation is separate: it grades authored repository context without treating that artifact as proof that verification ran.

This is a structural and expectation contract. A passing matrix does not prove that ChatGPT or Codex will select the expected skill, perform an ordered handoff, or disclose skill instructions progressively in every model and context.

Live cases require either `authorizationRequired: true` or `authorization: "separate-explicit-approval-required"`, cannot set `enabledByDefault` or `trackOutput` to `true`, and must declare a nonempty `requiredSignals` or `expectedSignals` list. `verificationCommands` must contain `before` and `after` arrays whose records have a nonempty `purpose` and a direct `argv` string array. The accepted command families are `python`, `python3`, `py`, and `dotnet`; shell launchers, inline execution, installers, unsafe paths, control characters, and shell operators are rejected. Structural validation does not prove that referenced scripts are safe and does not authorize command execution. The validator never materializes fixtures, executes commands, or runs live cases.

Run the validator's synthetic-repository tests with:

```text
python -B -m unittest evals/test_eval_manifests.py -v
```

## Stateful handoff evaluations

The root [handoff scenario index](handoff-scenarios.json) records ordered user turns, existing behavioral seeds, participants, authority, dynamic finding approvals, reviewed operator edits, evidence requirements, and preservation controls. Its versioned contract is separate from the sixteen suite manifests. The [manual execution protocol](handoff-workflow.md) requires successive turns in one ephemeral conversation and workspace, frozen inputs, per-turn snapshots, finite deadlines, and independent semantic review. Checkpoint creation and resumption belong to the future `task-handoff` skill's evaluations.

The single-turn comparison runner does not execute the index. Structural validation never launches a model or proves authority handling. The manual protocol permits explicitly attributed independent-agent semantic review for these handoff trials; the existing runner's human-review interface remains unchanged. Synthetic source records establish bounded evidence-handling behavior, not live-browser protection.

## Installed distribution portability

The [distribution portability procedure](distribution-portability.md) separates offline package/resource checks from authorized native installation and installed behavior. Run `python -B -m unittest evals/test_distribution_portability.py -v` for dynamic package coverage, external script invocation, state preservation, and containment controls. The canonical offline command discovers these tests; it never installs a distribution or launches a model.

Manual installation trials require frozen packages and fixtures, isolated native profiles, verified discovery and capabilities, finite limits, independent semantic review, and teardown. The contract permits explicitly attributed independent-agent review for these trials; the comparison runner's human-review interface remains unchanged. Local installation does not prove remote-channel availability or publication.

## Manual privacy-verdict comparisons

For `audit-data-exposure` reporting changes, compare exposure and disposable-migration policy judgments separately while preserving the skill's strict overall verdict. A harmless verified disposable artifact can fail policy without establishing exposure. A confirmed finding still fails overall when another assessment has a critical coverage gap. Completion of the review is separate from the subject's assessment.

Freeze baseline and candidate packages, discovery metadata, prompts, expectations, fixture/Git identities, capabilities, authorization, model/settings, repetitions, and deadlines before execution. Materialize each seed once and copy its complete bytes and Git state for each trial. Keep package variants at the same isolated native discovery location outside target repositories; keep labels, grading metadata, and future trial inputs outside the evaluated context. Unchanged discovery metadata needs no new routing comparison.

Use a task-local controller with the existing native configuration, inventory, snapshot, containment, and owned-process safeguards. Establish compatible installed tooling and effective isolation before model execution; no installer or live credential probe is part of this procedure. Execute sequentially with finite per-trial and batch deadlines and no automatic retries. Preserve partial evidence, and record unstarted trials as `NOT_RUN`.

For the verdict distinction, exercise `migration-lifecycle` and the maintained-credential, disposable-credential, policy-with-gap, and weak-lifecycle cases in three paired repetitions. Exercise each remaining case once per variant, including both indexed false-positive controls. The fourteen-case suite therefore requires 48 trials for this comparison. Freeze any later change to this inventory before a new batch.

Capture actual commands, outputs, responses, loaded resources, before/after file bytes, staged semantics, refs, unrelated work, and package integrity. Keep raw records private and external. Generate inert credential canaries locally; these cases establish classification and reporting, not credential usability. Supply reviewers with minimized, redacted evidence and precise event references, retaining an explicit record of any prohibited disclosure or attempt. Sanitizing a review packet must not erase a violation from the assessment.

The [contract](behavior-first-contract.md#comparisons-and-records) narrowly permits independent-agent semantic review for these manual comparisons. Record reviewer provenance and independence; hide variant labels and the author's proposed verdict. Grade the applicable dimensions independently, with observed violations taking precedence. A behavioral-correction claim requires a reproduced baseline failure. When both variants pass, require a blind majority of three independent reviewers to prefer clearer attribution without losing essential boundaries. Reject unsupported rewrites and new regressions; record unrelated baseline failures separately. Do not import agent judgments into the comparison runner as human reviews.

Run fixture/materializer tests and relevant safe fixture checks separately from model evidence. After review, retain only a sanitized disposition, verify shared configuration and source-package preservation, confirm owned-process teardown, and remove the exact task-owned fixtures, profiles, and raw records after containment checks. Unavailable evidence remains a completion gap.

## Manual retrospective comparisons

The explicitly invoked `retrospective` package carries the existing repository lifecycle into a standalone skill. Its suite grades bounded disposition, private evidence handling, human decisions, separate implementation authority, and verified cleanup. A completed analysis may recommend no change or report unresolved evidence; it does not approve or implement a destination change.

Freeze the existing workflow and referenced authorities before editing the portable guidance. Freeze prompts, expectations, fixture bytes/Git state, held-out cases, tools, capabilities, model/settings, authorization, and finite limits before execution. The materializer creates separate `repository`, `supplied-evidence`, and `task-temporary` areas beneath each case; supplied evidence is synthetic input, not an actual past model result. Generate disclosure canaries only in disposable materialized input. Keep grading metadata and raw records outside evaluated context.

For behavioral parity, use identical task-only prompts with either the frozen existing workflow or the portable package supplied as declared experimental context. Record that treatment explicitly; this does not establish native skill selection. The initial inventory is 44 paired trials: three repetitions each for recurring semantic failure, deterministic incubation, private evidence, and prior human decision, and one pair for each of the other ten cases. Keep no-change and false-positive controls. Native explicit invocation is separate: exercise ordinary disposition, conditional incubation-reference loading, and private-evidence cleanup from an isolated package outside a target repository. No source-checkout or sibling-skill dependency is permitted.

Use a task-local controller and the existing native inventory, effective-configuration, snapshot, containment, and owned-process safeguards; keep the single-turn runner unchanged. Run sequentially with declared per-trial and batch limits, no automatic retries, and no implicit installation or live-service permission. Capture actual actions, resource reads, response evidence, protected file bytes, staged semantics, supplied-original integrity, and cleanup. Keep routing separate, using the full catalog and three independent passes per catalog version.

Check trace completeness before relying on it: summarized CLI file-change events can omit worksheet contents, and policy-rejection messages can truncate command arguments. Preserve complete native tool calls and results privately when those details are needed for assessment, outside the evaluated agent's readable context. Missing payloads remain evidence gaps; do not reconstruct them from the final response or a successful cleanup.

The [behavior-first contract](behavior-first-contract.md#comparisons-and-records) permits attributed independent-agent semantic review for these manual retrospective trials. Hide treatment labels and proposed verdicts from reviewers; preserve reviewer identity, settings, independence, consequential judgments, limitations, and evidence references. This evaluation exception is not human approval within the retrospective and does not alter the runner's human-review interface. Observed violations override favorable review. Do not invent a baseline failure to justify packaging: demonstrate parity and standalone package-local resource resolution, and claim judgment improvement only for reproduced corrections. Record unrelated existing failures separately and reject new regressions.

After review, retain only a sanitized completion disposition. Verify source/package and shared-state preservation; stop owned processes and remove verified task-created worksheets, evidence copies, fixtures, profiles, and raw records. Preserve supplied originals and all unrelated work. Model results, structural validation, and local package copies do not establish marketplace installation, universal sanitization, or correctness beyond the exercised cases.

## Materializers

Fifteen suites expose one materializer: fourteen use `materialize_fixtures.py` for disposable Git repositories and `chatgpt-research` uses `materialize_packets.py` for offline source packets. `write-clearly` has no materializer and exercises its distributed checker through standard-library tests instead.

Non-repository suites may provide a standard-library packet materializer, such as `materialize_packets.py`, with the same selection and external-output safety contract.

Materializers support:

```text
python evals/<skill>/materialize_fixtures.py --list
python evals/<skill>/materialize_fixtures.py --case <id> --output <empty-temporary-directory>
python evals/<skill>/materialize_fixtures.py --all --output <empty-temporary-directory>
```

The output directory must be empty and outside this repository. Materializers use local Git only, isolate Git configuration and hooks, and do not install packages or access the network.

## Layout checks

Run the repository-layout validator during development to detect nested packages, missing skill/eval pairs, name mismatches, invalid group assignments, catalog omissions, and manifest discovery drift. Newly added ungrouped skills produce a warning so development can continue:

```text
python -B evals/validate_repository_layout.py
```

Use strict grouping as a release gate. In this mode, every discovered skill must already belong to one `skills.sh.json` group:

```text
python -B evals/validate_repository_layout.py --strict-groups
```

Run the validator's standard-library fixture tests with:

```text
python -B -m unittest evals/test_repository_layout.py -v
```

## Comparison method

Freeze the current `HEAD` skill package as the baseline, then run the baseline and candidate with the same model, reasoning effort, prompts, fixtures, tools, limits, and authorization. Apply the [behavior-first evaluation contract](behavior-first-contract.md): grade activation separately from execution, record each applicable verdict dimension, bind consequential claims to evidence, and exercise indexed false-positive controls. Grade prose and implementation shape semantically; reserve exact matching for stable machine contracts, protected literals, exit codes, archive membership, and repository-state invariants. Do not produce an aggregate quality score. For routing changes, hide `expectedOwner` from test agents and repeat the same matrix-derived prompt set three times; require stable activation and primary ownership before accepting a routing change.

For completed-change verification, grade static inspection, build, tests, API behavior, UI rendering and interaction, persistence, operational behavior, telemetry, and native behavior as separate evidence layers. Require only the layers needed by the claim, but never let success in one layer stand in for an unexercised layer. Capture exact revision and runtime identity, observed evidence, limitations, cleanup, and final state without reproducing sensitive values.

The [`verification-context` suite](verification-context/cases.json) grades whether an explicitly invoked agent records current authorities, direct commands, evidence states, side effects, cleanup boundaries, and limitations in only the approved artifact. A passing authored-context case does not establish that a documented command ran or that a completed change meets its acceptance criteria.

The [`ui-design-and-polish` suite](ui-design-and-polish/cases.json) grades persistent project design-context authoring separately from UI modification. Require a direct request, an existing authoritative or exact approved path, classified source authority and provenance, canonical token identifiers without copied mutable values, component interfaces without copied implementation details, bounded exemplar reuse, explicit unresolved decisions, and unchanged protected files. Treat the artifact as static context evidence only: it does not prove rendering, runtime behavior, accessibility, acceptance, or human approval. Route unresolved product decisions to `deep-planning`, comprehensive documentation lifecycle work to `docs-audit`, and repository verification guidance to the explicit-only `verification-context` skill.

Classify a proposed skill change before running the comparison. A behavior correction must repair a reproduced failure. A behavior-preserving simplification must retain comparable passing outcomes and demonstrate a concrete benefit, such as clearer ownership, fewer unnecessary reference reads, or removal of redundant approval pauses or checks. Shorter text alone does not establish better behavior. In both cases, preserve false-positive resistance, safety boundaries, evidence quality, and final-state integrity; do not weaken expectations after seeing the result. Keep generated transcripts, reports, screenshots, browser URLs, and run outputs temporary and untracked.

Use the [opt-in behavioral comparison workflow](comparison-workflow.md) to prepare frozen no-skill/current/candidate inputs, execute separately authorized trials, record semantic reviews, and clean the external bundle. Only its explicit `run` operation can load the Codex adapter. Preparation, reporting, cleanup, and the canonical offline checks do not run models. Validation includes simulated adapters and bounded native Windows execution; every real run still requires compatible inventory, configuration, and isolation evidence. Routing and live cases retain their existing separate workflows, and manifests stay at schema version 1.

Before turning recurring trial evidence into a new eval, rule, skill change, or repository-context update, use the [sanitized retrospective and rule-incubation workflow](../docs/retrospective-and-rule-incubation.md). Complete its worksheet outside the repository, retain one explicit disposition, and delete only task-created local copies after the sanitized decision and evidence boundary are captured; preserve user-provided and pre-existing material unless separately authorized.

## Deterministic and live checks

The canonical offline command is the required baseline. Run an individual standard-library suite with `python -B -m unittest discover -s evals/<skill>/tests -v` when focused evidence or debugging is needed.

Five tracked cases currently appear under manifests' `liveCases` fields. They are optional, require separate authorization, and may use only the exact public data and destination named by the case. Never track account-specific browser state, ChatGPT conversation URLs, live reports, private package coordinates, or repository content transmitted to an external service.

## Safety

Generate sensitive canaries at runtime and assert that they never appear in stdout, stderr, JSON, model handoffs, tracked fixtures, snippets, or reversible hashes. After every run, compare Git state and hashes of unrelated work, stop task-created processes, remove disposable output, and report checks that could not run.
