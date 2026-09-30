# Focused product-UI comparisons

TODO-016 adds paired task-quality evidence under the existing UI owner. Follow the [behavior-first contract](../behavior-first-contract.md) and [verification map](../../docs/verification.md). These cases use the unchanged distributed skill; they do not demonstrate a skill improvement merely by adding evaluations.

## Four exercised cases

| Case | Comparison and protected behavior |
| --- | --- |
| `operational-table-refine` | Improve unnecessarily spacious operational presentation while retaining aligned comparison, all twelve records and columns, sorting, filtering, selection and matching evidence. |
| `justified-cards-refine` | Preserve an already-usable conventional grouping for independent tasks; a justified unchanged result is required. Native disclosure and keyboard focus remain usable. |
| `generic-workflow-refine` | Compare supplied short and long Danish titles under matched layouts; preserve the original long title, evidence, test hooks, approval and rejection paths. |
| `permission-state-refine` | Compare allowed and denied client states; retain full explanations, read-only evidence, guarded actions, confirmation, cancellation and focus return. |

The existing justified-pattern, blocked-rendering and context cases remain intact. The new card control is indexed alongside existing false-positive controls. Fixtures contain explicitly synthetic content, not new product claims. Query parameters select fixture states; they do not demonstrate server authorization or persistence.

Judge task consequences rather than component popularity, arbitrary density targets, authorship, numerical taste scores or screenshot goldens. A comparison table can keep a contained horizontal scroller when its relationships require it; other content must reflow. See [W3C Reflow guidance](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html), reviewed 2026-09-30. A browser pass is not formal accessibility conformance.

## Authorized focused procedure

Freeze the skill packages, discovery metadata, prompts, expectations, fixture bytes and complete Git state, capabilities and limits before execution. Keep grading expectations and case labels outside evaluated workspaces. Prepare each seed once with staged, unstaged, untracked and ignored sentinels; supply independent external package copies. Preflight resource closure and observe the intentional fixture weaknesses and legitimate controls before grading an agent.

Run the four cases once, sequentially, using requested `gpt-6-astra`/high. Each evaluated trial has 300 seconds; the complete evaluation window, including one independent review, has 25 minutes. No retries, deadline extensions or guidance-correction campaign. Prefer fresh agents; if capacity prevents this, reuse idle agents with separate workspaces and disclose retained context. The reviewer must not author the fixtures or evaluated responses. Record requested settings separately from runtime attestation.

Use the fixture's documented standard-library loopback server. Capture matched screenshots and DOM evidence at 1280 by 720 and 375 by 812 before and after changes, including both Danish content lengths and both permission states. Exercise sorting, filtering, hidden-row selection, evidence identity, keyboard focus, disclosures, cancellation and confirmation where applicable. Inspect wrapping, clipping, scrolling and action availability. Record additional accessibility checks and missing evidence explicitly; do not substitute source assertions for browser observations. Only authorized HTML/CSS may change, and the justified-card control should remain byte-identical.

Keep complete final reports, available action evidence, command output, state comparisons and actual captures in an owned external directory until review. Give the independent reviewer neutral capture ordering, complete reports rather than summaries, the declared requirements and evidence limits. Grade task outcomes, reporting completeness, claim support, authority, scope and preservation under existing verdict precedence. Activation is not applicable because discovery is unchanged. Distinguish browser observations, parent replays, agent reports and unavailable traces. A correctly bounded report of missing evidence does not establish the missing rendered requirement.

The independent-agent review is a scoped exception, not human review or an alteration of the comparison runner's human-review interface. Record reproduced skill failures separately; missing evidence or an unmet condition keeps focused completion open. No new general runner, dependency, host configuration or publication step is included.

After review, stop owned servers, close created tabs, reset viewport overrides and remove ownership-verified fixtures, package copies, captures and raw records. Preserve unrelated work. Full suites, canonical offline orchestration, broad routing, native isolation, broader distribution/release coverage and the unavailable plugin validator remain deferred for personal development.

## Focused maintenance checks

From the repository root:

```text
python -B evals/validate_eval_manifests.py
python -B evals/ui-design-and-polish/materialize_fixtures.py --list
python -B -m unittest discover -s evals/ui-design-and-polish/tests -p test_product_ui_fixtures.py -v
git diff --check
git status --short --branch
```

Materialize only the four selected cases with repeated `--case <id>` and `--output <empty-external-directory>`. The focused preparation checks reuse existing containment, Git-state and cleanup helpers and check local resource closure; they launch no browser, service, installer or model and prove no rendered behavior. Review resources, metadata, the complete diff and final state separately. Guidance/package validation is unnecessary for unchanged distributed files.
