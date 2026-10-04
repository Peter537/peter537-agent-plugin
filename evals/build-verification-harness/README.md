# Verification-harness evaluations

These maintenance fixtures assess authoring useful proof, not independent acceptance of a product. They are not distributed with the skill. The [behavior-first contract](../behavior-first-contract.md) and [verification map](../../docs/verification.md) remain authoritative.

## Focused personal-development procedure

The authorized harness-authoring inventory is four smoke cases, once each: missing persistence proof, a passing ineffective assertion, adequate existing proof, and unavailable rendered-browser capability. Run the fourteen declared `triggerCases` once per frozen baseline/candidate catalog, exposing each complete catalog and invocation policy while hiding expectations. Absence of the new skill in the baseline is an availability gap, not a regression. Existing owners must remain stable; explicit-only skills must not activate implicitly.

Freeze packages, discovery metadata, prompts, expectations, fixture bytes and Git state, capabilities, and limits before execution. Materialize each seed once outside the checkout and copy complete bytes and Git state to a neutral disposable workspace. Supply an independent package copy; keep labels, grading records, and other packages outside the evaluated workspace/context. The no-op and unavailable-capability cases are false-positive controls.

Use fresh subagents, sequentially, with `gpt-6-astra`/high requested, a 240-second behavioral-trial limit, and a 20-minute total model-execution budget. Allow at most one narrow correction and one affected rerun within that budget. No blind retries or extensions. This procedure intentionally skips native CLI isolation setup. Record configured identity separately from any independently attested runtime identity.

Capture pre/post file bytes, staging semantics, refs, ignored/untracked work, package integrity, responses, and available action evidence. Independently replay authored checks in disposable copies: prove the persistence fault fails for a value mismatch, and wrong parser contents pass the original weak assertion but fail the stronger one. Restore original production bytes and require green checks afterward. Synthetic faults are infrastructure experiments, not historical product defects. Parent replays and final snapshots do not establish an exhaustive intermediate action trace or filesystem isolation.

One fresh independent agent reviews neutral responses, actual artifacts, state comparisons, and replay evidence, without the author's proposed verdict. Record reviewer identity, requested model/settings, independence, consequential judgments, evidence references, and limitations. Observed violations override favorable review; do not label this human review or import it into the comparison runner's human-review interface.

Cleanup only verified task-owned roots after review, checking containment and links and preserving supplied originals and unrelated state. Preserve incomplete evidence as a gap. The user deferred full suites, canonical offline validation, full-catalog routing, repeated comparisons, native isolation, installed-distribution refresh, and the unavailable bundled plugin validator. These focused checks do not replace release gates.

## Fixture checks

From the repository root, with Python 3, local Git, and writable external temporary storage:

```text
python -B evals/build-verification-harness/materialize_fixtures.py --list
python -B evals/build-verification-harness/materialize_fixtures.py --all --output <empty-external-directory>
python -B -m unittest discover -s evals/build-verification-harness/tests -v
```

Preparation uses the [shared state helpers](../comparison_state.py), preserves staged/unstaged differences, and adds unrelated untracked, ignored, and runtime files. It never interprets setup prose as commands, launches models, installs tools, or starts services. Preparation tests establish containment and fixture/fault authenticity, not skill behavior.

The Counter fixture adapts the existing [verification-context Counter fixture](../verification-context/fixtures/cli-restart-context-create/base/counter.py) to separate-process storage proof. The parser and unavailable-browser fixtures are synthetic. Their contracts, checks, and allowed paths are defined independently of model output. No fixture assertions or expectations belong inside the distributed skill.
