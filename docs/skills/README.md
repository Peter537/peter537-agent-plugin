# Skill Catalog

This catalog organizes the plugin's skills for readers without changing their installable layout. Agent Plugin discovery requires each package to be an immediate child at `skills/<slug>/SKILL.md`; nested category packages can fail with `skill_manifest_nested`. The matching maintenance evaluations stay flat at `evals/<slug>/cases.json`. See [Build skills](https://developers.openai.com/plugins/build/skills) and [skill submission errors](https://developers.openai.com/plugins/deploy/submission-errors#skill-errors).

[`skills.sh.json`](../../skills.sh.json) is the machine-readable source for the groups below. Its `notGrouped: "bottom"` setting keeps newly added skills discoverable during development until they are assigned to a group; strict layout validation makes an ungrouped skill release-blocking.

## Planning & research

| Skill | Purpose | Evaluation |
| --- | --- | --- |
| [`deep-planning`](../../skills/deep-planning/SKILL.md) | Research and clarify complex software changes before implementation. | [`cases.json`](../../evals/deep-planning/cases.json) |
| [`chatgpt-research`](../../skills/chatgpt-research/SKILL.md) | Orchestrate and verify multi-source ChatGPT Deep Research. | [`cases.json`](../../evals/chatgpt-research/cases.json) |

## Engineering quality

| Skill | Purpose | Evaluation |
| --- | --- | --- |
| [`deep-code-audit`](../../skills/deep-code-audit/SKILL.md) | Audit correctness, security, architecture, maintainability, and change quality across a codebase or scoped change. | [`cases.json`](../../evals/deep-code-audit/cases.json) |
| [`diagnose-bugs`](../../skills/diagnose-bugs/SKILL.md) | Reproduce, localize, diagnose, and repair concrete local or CI defects with regression evidence. | [`cases.json`](../../evals/diagnose-bugs/cases.json) |
| [`comment-health`](../../skills/comment-health/SKILL.md) | Audit and safely improve source comments without losing contracts, rationale, documentation, or tool semantics. | [`cases.json`](../../evals/comment-health/cases.json) |
| [`prune-codebase`](../../skills/prune-codebase/SKILL.md) | Prove and retire dead or obsolete repository surface without guessing about consumers or compatibility. | [`cases.json`](../../evals/prune-codebase/cases.json) |
| [`reduce-code-slop`](../../skills/reduce-code-slop/SKILL.md) | Review and simplify scoped C# and Python code without changing established behavior. | [`cases.json`](../../evals/reduce-code-slop/cases.json) |

## Security & supply chain

| Skill | Purpose | Evaluation |
| --- | --- | --- |
| [`audit-dependencies`](../../skills/audit-dependencies/SKILL.md) | Review every dependency and software supply-chain input before package changes or on request. | [`cases.json`](../../evals/audit-dependencies/cases.json) |
| [`audit-data-exposure`](../../skills/audit-data-exposure/SKILL.md) | Review current repository content and reachable Git history for personal data, private artifacts, anonymization failures, and disposable migrations. | [`cases.json`](../../evals/audit-data-exposure/cases.json) |

## Documentation & writing

| Skill | Purpose | Evaluation |
| --- | --- | --- |
| [`docs-audit`](../../skills/docs-audit/SKILL.md) | Audit and rebuild repository documentation against implementation evidence. | [`cases.json`](../../evals/docs-audit/cases.json) |
| [`write-clearly`](../../skills/write-clearly/SKILL.md) | Draft, edit, and audit repository prose for clarity, reader fit, fidelity, and voice in its source language. | [`cases.json`](../../evals/write-clearly/cases.json) |

## UI & .NET

| Skill | Purpose | Evaluation |
| --- | --- | --- |
| [`ui-design-and-polish`](../../skills/ui-design-and-polish/SKILL.md) | Design, audit, refine, and verify accessible product interfaces. | [`cases.json`](../../evals/ui-design-and-polish/cases.json) |
| [`maui-blazor-browser`](../../skills/maui-blazor-browser/SKILL.md) | Develop and verify MAUI Blazor Hybrid UI through a safe Web companion or temporary browser harness. | [`cases.json`](../../evals/maui-blazor-browser/cases.json) |

## Adding a skill

- Create one immediate `skills/<slug>/` directory with a matching `SKILL.md`; do not add category directories or nested skill packages.
- Add the matching maintenance suite at `evals/<slug>/cases.json`.
- Assign the slug to exactly one group in [`skills.sh.json`](../../skills.sh.json).
- Add its package, purpose, and evaluation links to this catalog.
- Run the repository-layout checks, the skill validator, the complete plugin validator, and every applicable check in the [repository verification map](../verification.md).
- During release preparation, update the applicable manifests, installation guidance, submission copy, evaluation bundle, and release notes.
