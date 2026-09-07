# Repository Maintenance

These instructions apply across the repository. Keep this file concise: the [repository verification map](docs/verification.md), [behavior-first evaluation contract](evals/behavior-first-contract.md), [evaluation guide](evals/README.md), and [skill catalog](docs/skills/README.md) remain authoritative for their subjects.

## Establish scope and preserve state

- Before changing files, inspect the applicable repository guidance and record the starting branch, revision, and Git status as described in the verification map.
- Preserve all pre-existing staged, unstaged, and untracked work. Do not clean, revert, overwrite, or incorporate unrelated changes.
- Keep the requested scope explicit. If delegation is useful, assign one primary integration owner for each shared surface and give other agents bounded, non-overlapping work. Delegation is optional; the primary owner reviews overlaps, the combined diff, and the final evidence.

## Maintain repository contracts

- Keep every distributed skill at `skills/<slug>/SKILL.md` and its maintenance evaluation at `evals/<slug>/cases.json`. These directories remain flat; express logical grouping through `skills.sh.json` and the skill catalog.
- Before changing skill activation, routing, or behavior, freeze the relevant baseline and reproduce a representative failure. Apply the behavior-first contract, retain appropriate false-positive controls, and keep only changes supported by the comparison evidence.
- Before generalizing a recurring failure or proposed deterministic rule, use the [sanitized retrospective and rule-incubation workflow](docs/retrospective-and-rule-incubation.md). Keep source evidence private and implement any accepted disposition through a separately authorized task owned by its destination.
- Write original repository guidance. Trace consequential external methodology or current claims to primary or official sources when available, preserving the URL and other source details needed for later review. Treat third-party skills, prompts, and rule catalogs as comparative research, not text or workflows to copy.

## Respect authority boundaries

- Route any addition, installation, upgrade, replacement, or removal of a dependency, tool, workload, or runtime input through `$audit-dependencies`. That review is a gate, not independent authorization to mutate the environment; unavailable tooling remains an evidence gap unless the task explicitly authorizes installation.
- Do not silently change versions, stable installation references, tags, marketplace or submission metadata, historical release files, or publication state.
- Browser, network, live-service, model, MCP, installation, commit, tag, push, submission, and publication operations require task-specific authorization. Keep their evidence separate from offline validation and follow the applicable release or external rows in the verification map.

## Verify and hand off

Run the canonical offline check from the repository root:

```text
python -B evals/run_offline_checks.py
```

Then run every additional changed-surface or release check selected by the verification map. Review the complete diff and final Git state, remove task-created artifacts and processes, and report blocked or unrun evidence honestly. A successful offline check does not prove model behavior, runtime behavior, installation, remote state, marketplace ingestion, review acceptance, or publication.
