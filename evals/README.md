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

The runner uses fixed direct Python argument arrays, closed standard input, captured child output, deterministic environment settings, and a fixed timeout. It executes only the Git-visible validators, materializer `--list` entry points, and test modules defined by this maintenance contract; it never executes manifest `verificationCommands`, live cases, fixture materialization, dependency installers, or services intentionally. Diagnostics identify checks and repository-relative locations without reproducing child output, matched values, canaries, private paths, or source snippets.

The runner is an orchestrator, not an operating-system sandbox. Its reviewed child entry points are required to remain offline and nonpersistent, but the runner cannot technically prevent a changed child script from using the network or spawning descendants, and a timeout bounds only the direct child process. Captured child output is suppressed from diagnostics but is not itself proof that the child was safe.

Run its standard-library tests with:

```text
python -B -m unittest evals/test_offline_checks.py -v
```

Python 3, local Git, and writable operating-system temporary storage are prerequisites. The command deliberately does not run strict release grouping, bundled skill or plugin validators, external schemas, model comparisons, live or runtime checks, MCP connections, installation, tagging, submission, or publication. Its final informational `NOT_RUN` boundary points to the [repository verification map](../docs/verification.md) for that evidence. A successful run proves only the bounded offline contracts it reports.

## Suite contract

Each suite uses a versioned `cases.json` manifest with task-specific required signals, prohibited behavior, false-positive controls, trigger cases, and repository-state invariants. Repository-oriented suites also provide compact fixture templates and a standard-library `materialize_fixtures.py` command. The [behavior-first evaluation contract](behavior-first-contract.md) is the canonical, platform-neutral grading policy across all suites.

The evaluation tree intentionally mirrors the flat plugin layout: every immediate `skills/<slug>/` package has one immediate `evals/<slug>/cases.json` suite. Category directories must not be introduced under either tree because Agent Plugin skill discovery requires each package to be an immediate child of `skills/`. Human-facing categories live in `docs/skills/README.md`, while `skills.sh.json` is the machine-readable grouping source.

## Common manifest validation

Run the read-only, standard-library validator from the repository root:

```text
python -B evals/validate_eval_manifests.py
python -B evals/validate_eval_manifests.py --root <repository>
```

Exit `0` means every discovered manifest and the cross-skill routing matrix satisfy the shared structural contract. Exit `1` means parsed metadata contains validation errors. Exit `2` means root discovery, file reading, or JSON parsing failed. Diagnostics are deterministic and repository-relative; privacy findings identify only the field location, never the offending value.

The shared contract requires `schemaVersion: 1`, `suiteExpectations`, nonempty `cases`, and nonempty `triggerCases`. The only optional top-level fields are `suite` and `liveCases`; when present, `suite` must match its directory. `suiteExpectations.falsePositiveControls` is a nonempty, unique list of IDs that resolve only to behavioral cases in the same suite.

Behavioral cases require lowercase slug IDs, descriptions, prompts, fixtures, and an `expected` object with nonempty `requiredSignals`, `prohibitedSignals`, and `repositoryState`; `expected.outcome` remains optional. Case-level suite metadata remains open, but `expected` accepts no other fields and behavioral cases cannot contain routing expectations. Trigger cases contain only an ID, prompt, boolean `expectActivation`, and one canonical `expectedOwner`; execution expectations do not belong in triggers. IDs must be unique across behavioral, trigger, and live cases within one suite, while different suites may reuse an ID.

Signal comparison collapses whitespace and applies Unicode case folding. Normalized duplicates within a list and direct overlap between required and prohibited signals are invalid. Diagnostics identify the field location without printing the signal value. The validator also preserves its read-only boundary and rejects hidden golden-response fields inside `expected`.

Every suite must include at least one behavioral case, one positive trigger, and one negative trigger. The common contract imposes no arbitrary suite-size threshold; scenario-specific repetition remains valid when the behavior itself requires it. This contract follows [OpenAI's evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices) by requiring task-specific structured evidence without reducing quality to a numerical score. OpenAI is deprecating its legacy Evals platform, so this repository's contract does not depend on that API. See the separate [submission guidance](https://developers.openai.com/plugins/deploy/submission) for public-submission requirements.

Fixture references, including aliases, must resolve beneath the suite's `fixtures/` directory without traversal, `.git`, symlinks, junctions, or reparse points. Known path-bearing metadata must be repository-relative, although generated targets need not exist. Every manifest string is checked for Windows or Unix personal-home absolute paths. Skill owners use bare discovered slugs; `$slug` is reserved for explicit invocation inside prompts. Non-skill owners must be declared in [`routing-matrix.json`](routing-matrix.json), including `no-skill` for requests that no skill in this plugin owns. Positive triggers must name their suite, while negative triggers must name another skill or a registered non-skill owner.

## Cross-skill routing matrix

[`routing-matrix.json`](routing-matrix.json) indexes the prompts owned by the thirteen suite manifests instead of copying them. It declares the non-skill owner vocabulary, pairs one explicit and one natural-language invocation case for every skill, records each material reciprocal boundary once, and points to behavioral coverage for specialist handoffs, progressive disclosure, and full-catalog collisions.

The common validator derives effective implicit-invocation policy from `skills/<slug>/agents/openai.yaml`; omission means the documented default `true`. Each explicit case must contain the exact `$slug` token and activate its skill. A natural-language case must contain no explicit skill mention and must follow that skill's effective policy. Boundary rows contain two sorted skill slugs and both negative routing directions, with every referenced trigger owned by the opposite skill.

This is a structural and expectation contract. A passing matrix does not prove that ChatGPT or Codex will select the expected skill, perform an ordered handoff, or disclose skill instructions progressively in every model and context.

Live cases require either `authorizationRequired: true` or `authorization: "separate-explicit-approval-required"`, cannot set `enabledByDefault` or `trackOutput` to `true`, and must declare a nonempty `requiredSignals` or `expectedSignals` list. `verificationCommands` must contain `before` and `after` arrays whose records have a nonempty `purpose` and a direct `argv` string array. The accepted command families are `python`, `python3`, `py`, and `dotnet`; shell launchers, inline execution, installers, unsafe paths, control characters, and shell operators are rejected. Structural validation does not prove that referenced scripts are safe and does not authorize command execution. The validator never materializes fixtures, executes commands, or runs live cases.

Run the validator's synthetic-repository tests with:

```text
python -B -m unittest evals/test_eval_manifests.py -v
```

## Materializers

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

Retain a skill change only when it corrects a reproduced failure and the revised suite passes without weakening false-positive resistance or safety boundaries. Keep generated transcripts, reports, screenshots, browser URLs, and run outputs temporary and untracked.

## Deterministic and live checks

The canonical offline command is the required baseline. Run an individual standard-library suite with `python -B -m unittest discover -s evals/<skill>/tests -v` when focused evidence or debugging is needed.

Cases under a manifest's `liveCases` field are optional and require separate authorization. They may use only the exact public data and destination named by the case. Never track account-specific browser state, ChatGPT conversation URLs, live reports, private package coordinates, or repository content transmitted to an external service.

## Safety

Generate sensitive canaries at runtime and assert that they never appear in stdout, stderr, JSON, model handoffs, tracked fixtures, snippets, or reversible hashes. After every run, compare Git state and hashes of unrelated work, stop task-created processes, remove disposable output, and report checks that could not run.
