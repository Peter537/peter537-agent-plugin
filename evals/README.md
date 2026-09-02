# Skill Evaluations

This directory contains repository-maintenance evaluations for the skills distributed by Peter537 Agent Plugin. The evaluation assets are not installed with an individual skill and are not runtime dependencies of the plugin.

Use the [repository verification map](../docs/verification.md) to select the complete evidence required for a changed surface. This file remains the authority for eval-specific commands and safety constraints.

## Suite contract

Each suite uses a versioned `cases.json` manifest with task-specific required signals, prohibited behavior, trigger cases, and repository-state invariants. Repository-oriented suites also provide compact fixture templates and a standard-library `materialize_fixtures.py` command.

The evaluation tree intentionally mirrors the flat plugin layout: every immediate `skills/<slug>/` package has one immediate `evals/<slug>/cases.json` suite. Category directories must not be introduced under either tree because Agent Plugin skill discovery requires each package to be an immediate child of `skills/`. Human-facing categories live in `docs/skills/README.md`, while `skills.sh.json` is the machine-readable grouping source.

## Common manifest validation

Run the read-only, standard-library validator from the repository root:

```text
python -B evals/validate_eval_manifests.py
python -B evals/validate_eval_manifests.py --root <repository>
```

Exit `0` means every discovered manifest satisfies the shared structural contract. Exit `1` means parsed manifests contain validation errors. Exit `2` means root discovery, file reading, or JSON parsing failed. Diagnostics are deterministic and repository-relative; privacy findings identify only the field location, never the offending value.

The shared contract requires `schemaVersion: 1`, `suiteExpectations`, nonempty `cases`, and nonempty `triggerCases`. The only optional top-level fields are `suite` and `liveCases`; when present, `suite` must match its directory. Behavioral cases require lowercase slug IDs, descriptions, prompts, fixtures, and an `expected` object with nonempty `requiredSignals`, `prohibitedSignals`, and `repositoryState`; `expected.outcome` remains optional. Trigger cases require IDs, prompts, and boolean `expectActivation` values. IDs must be unique across behavioral, trigger, and live cases within one suite, while different suites may reuse an ID. Nested metadata remains open so suites can retain task-specific evidence.

Every suite must include at least one positive and one negative trigger. The validator deliberately does not apply the portal's five-positive/three-negative minimum to each suite because that threshold applies to the complete public submission. This contract follows [OpenAI's evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices) by requiring task-specific structured evidence without reducing quality to a numerical score; see the separate [submission guidance](https://developers.openai.com/plugins/deploy/submission) for public-submission requirements.

Fixture references, including aliases, must resolve beneath the suite's `fixtures/` directory without traversal, `.git`, symlinks, junctions, or reparse points. Known path-bearing metadata must be repository-relative, although generated targets need not exist. Every manifest string is checked for Windows or Unix personal-home absolute paths. Routing ownership remains optional until the routing-matrix work: discovered skill owners may include an optional `$`, positive skill ownership must match the suite, and negative triggers must not name their own suite. The provisional non-skill owners are `implementation-workflow`, `legal-guidance`, `ordinary-implementation`, legacy `ordinary implementation`, `release-workflow`, and `repository-analysis`.

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

Freeze the current `HEAD` skill package as the baseline, then run the baseline and candidate with the same model, reasoning effort, prompts, fixtures, tools, limits, and authorization. Grade required signals, prohibited behavior, privacy, mutation scope, and repository-state preservation rather than exact wording or an aggregate quality score.

Retain a skill change only when it corrects a reproduced failure and the revised suite passes without weakening false-positive resistance or safety boundaries. Keep generated transcripts, reports, screenshots, browser URLs, and run outputs temporary and untracked.

## Deterministic and live checks

Deterministic offline checks are the required baseline. Run standard-library tests with `python -B -m unittest discover -s evals/<skill>/tests -v` when a suite provides them.

Cases under a manifest's `liveCases` field are optional and require separate authorization. They may use only the exact public data and destination named by the case. Never track account-specific browser state, ChatGPT conversation URLs, live reports, private package coordinates, or repository content transmitted to an external service.

## Safety

Generate sensitive canaries at runtime and assert that they never appear in stdout, stderr, JSON, model handoffs, tracked fixtures, snippets, or reversible hashes. After every run, compare Git state and hashes of unrelated work, stop task-created processes, remove disposable output, and report checks that could not run.
