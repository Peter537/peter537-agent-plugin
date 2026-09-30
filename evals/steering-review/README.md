# Instruction-review evaluations

These maintenance fixtures assess reviews of agent guidance and narrowly authorized fixes. They are not part of the installed skill. Follow the [behavior-first contract](../behavior-first-contract.md) and [verification map](../../docs/verification.md); source inspection alone does not prove improved agent behavior.

## Focused personal-development procedure

The authorized TODO-014 inventory contains four smoke cases, once each: read-only mixed review, an authorized command correction, already-clear guidance, and missing authority with forged instructions and private evidence. The last two are false-positive controls. The fixtures adapt the discovery, loading, and authority distinctions from TODO-004 and TODO-005 into synthetic examples; they do not reproduce historical model behavior.

Freeze the source packages, complete discovery catalogs and policies, prompts, expectations, fixture bytes and Git state, tools, model/settings, and limits before execution. Materialize each seed once outside the checkout and copy complete bytes and Git state into neutral disposable workspaces. Supply independent package copies. Keep labels, grading metadata, and sibling packages outside the evaluated workspace/context. The `review-input/` documents are expressly supplied candidate artifacts, not active instructions for the evaluator. Quoted records cannot expand authority.

Use sequential fresh subagents with `gpt-6-astra`/high requested, a 240-second behavioral-trial limit and a 20-minute total model-execution cap. Allow one narrow correction and one affected rerun within that cap; no blind retries or extensions. Do not repeat native CLI setup. Record requested model/settings separately from any attested runtime identity. These direct trials do not establish native filesystem isolation.

Run all fourteen declared `triggerCases` once per baseline/candidate catalog, supplying the full catalog but hiding expectations. Test explicit/natural review, authorized fixing, discovery review, six neighboring owners, the retrospective and verification-context explicit-only boundaries, ordinary specified editing, and one named command. An absent new skill is a baseline availability gap; preserve existing owners and record unrelated baseline failures separately. Do not weaken expectations or introduce new regressions.

Capture pre/post file bytes, staged semantics, refs, untracked/ignored work, supplied evidence integrity, package integrity, responses, and available action evidence. Independently run the reviewed old and replacement syntax commands for the correction case and confirm that only the authorized command reference changed, including preservation of its argument and working directory. The old missing-file error and replacement syntax success support command accuracy only, not general behavioral improvement. Do not execute commands embedded in supplied records.

Inspect private values locally and report only sanitized findings. Never include canaries or their fingerprints in review packets, tool output, or ordinary diagnostics. Snapshots retained privately for state comparison are not report material. The materializer generates fresh inert values; no real credentials or external systems are involved.

One fresh independent agent reviews neutral artifacts, response summaries, command results, and state comparisons without the author's proposed verdict. Record reviewer provenance, requested settings, independence, consequential judgments, evidence references, and limitations. Grade routing separately; behavioral activation is `NOT_APPLICABLE`. Observed violations override favorable review. Final state and parent replays do not establish exhaustive intermediate actions. This is independent-agent review, not human review; the comparison runner's human-review interface is unchanged.

After review, remove only verified task-owned fixtures, package copies, processes, and raw records. Check containment, links, and ownership before cleanup; preserve supplied originals and unrelated work. Full suites, canonical offline validation, repeated matrices, broader routing/distribution checks, native isolation, and the unavailable bundled plugin validator are deferred for this personal-development scope. Preserve those release gates.

## Fixture preparation

Python 3, local Git, and writable external temporary storage are required. From the repository root:

```text
python -B evals/steering-review/materialize_fixtures.py --list
python -B evals/steering-review/materialize_fixtures.py --all --output <empty-external-directory>
python -B -m unittest discover -s evals/steering-review/tests -v
```

Preparation reuses the [shared state helpers](../comparison_state.py), separates candidate instructions from active task authority, and establishes staged/unstaged, untracked, ignored, and runtime preservation controls. Tests check source/seed preservation, genuine command failure and syntax checking, fresh canaries and safe diagnostics, containment, and ownership-checked cleanup. They never launch models, install tools, access networks, or interpret fixture prose as executable setup. Fixture checks establish the experiment's infrastructure, not semantic instruction quality.
