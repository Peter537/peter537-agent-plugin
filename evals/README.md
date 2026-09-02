# Skill Evaluations

This directory contains repository-maintenance evaluations for the skills distributed by Peter537 Agent Plugin. The evaluation assets are not installed with an individual skill and are not runtime dependencies of the plugin.

Use the [repository verification map](../docs/verification.md) to select the complete evidence required for a changed surface. This file remains the authority for eval-specific commands and safety constraints.

## Suite contract

Each suite uses a versioned `cases.json` manifest with task-specific required signals, prohibited behavior, trigger cases, and repository-state invariants. Repository-oriented suites also provide compact fixture templates and a standard-library `materialize_fixtures.py` command.

The evaluation tree intentionally mirrors the flat plugin layout: every immediate `skills/<slug>/` package has one immediate `evals/<slug>/cases.json` suite. Category directories must not be introduced under either tree because Agent Plugin skill discovery requires each package to be an immediate child of `skills/`. Human-facing categories live in `docs/skills/README.md`, while `skills.sh.json` is the machine-readable grouping source.

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
