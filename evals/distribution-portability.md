# Installed distribution portability

Use this procedure to establish whether the same frozen skill packages work outside their source checkout. Package copying, installation, and installed behavior are separate evidence layers. The single-turn comparison runner does not install distributions or execute this procedure.

## Offline package checks

```text
python -B -m unittest evals/test_distribution_portability.py -v
python -B -m unittest discover -s evals/write-clearly/tests -v
python -B evals/run_offline_checks.py
```

The maintenance tests discover the current packages dynamically. They check independent copies, the complete plugin's runtime files, and the skills-only archive allowlist: `.codex-plugin/plugin.json`, `skills/`, and `assets/logo.png`. Every package must resolve its own Markdown references and declared assets without repository documentation or sibling packages. Copies retain source bytes; the full form retains marketplace and MCP definitions, while the skills-only form excludes them.

Installed-location tests run the three bundled Python scripts against separate disposable repositories. They reuse the prose checker's clean and dirty controls and check dependency inventory and redacted exposure scanning. Paths contain spaces. Package bytes, staged semantics, unrelated tracked work, untracked files, and ignored files must survive. Negative controls cover missing or escaping resources, unsafe destinations and links, ownership, and failed cleanup. A child-launch canary permits only fixture Git operations and byte-matching bundled scripts; it rejects installers, models, and services. This is a test boundary, not an operating-system network sandbox. Report host-dependent link-test skips.

The canonical offline command discovers this test module normally. Neither it nor these tests executes an installation or model trial.

## Freeze an authorized installation batch

Before invoking an installer, apply `audit-dependencies` to its exact executable and dependency graph. Installation and model execution need task-specific authorization. Prefer already available, verified tools; unavailable tooling does not authorize a download or upgrade.

Create a task-owned external root and an ownership record. Freeze source revision and dirty state, all package bytes, distribution membership, fixtures and their complete Git state, prompts, expectations, permissions, capabilities, tool versions, model settings, trial inventory, and finite deadlines. Preserve source and user-configuration baselines privately. Keep grading metadata, trial labels, later review records, and the source evaluation tree outside the target repository and agent-supplied context.

Materialize each selected fixture once with its reviewed existing materializer, then copy that complete seed for each distribution. `write-clearly` uses explicitly prepared seeds instead. Preserve original authority and expectations; declare any path-only prompt adjustment before execution. Do not tell the agent how to invoke an installed resource. A no-op and a correctly reported missing capability are useful controls.

## Install through native mechanisms

Use fresh child-process homes, profiles, state directories, and caches outside the source checkout. Disable installer telemetry and security-audit submissions. Do not alter the user's configuration, credentials, installed plugins, or unrelated caches. Do not start MCP servers, provision browsers, install dependencies automatically, or initiate external authentication flows.

| Form | Procedure and required evidence |
| --- | --- |
| Individual skills | Invoke the audited Skills CLI against the frozen local source, selecting one skill and Codex with `--global --copy --yes`. Give each skill its own profile. Verify the actual native installation path, package bytes, resource closure, and discovery without siblings; do not infer the destination from another CLI version. |
| Complete plugin | Add the frozen local marketplace with the installed Codex CLI and install the named plugin. Verify all expected skills and packaged MCP definitions. Definition presence is not server startup or tool behavior. |
| Skills-only bundle | Verify archive integrity, allowlisted membership, and byte parity; extract into a new owned directory. Install through a disposable local marketplace wrapper outside the archive. Verify all expected skills and the absence of bundled MCP definitions. The wrapper is test infrastructure, not submission content. |

These mechanisms follow the [Codex local marketplace workflow](https://developers.openai.com/plugins/build/plugins#marketplace-metadata) and [Skills CLI local-source options](https://github.com/vercel-labs/skills). Skills CLI documents `DISABLE_TELEMETRY` and `DO_NOT_TRACK`; verify the behavior of the exact audited version. CLI exit zero alone does not prove installation: inspect its results and installed files.

Before starting any model, verify the installed host's effective configuration, native skill inventory, enabled capabilities, and package provenance. Use process-local overrides for unwanted exposure. Duplicate skills, missing resource identity, or unverified isolation block execution. Do not substitute workspace skill overlays or treat an ignored configuration file as isolation proof. Keep bundled servers disabled even when the plugin is installed.

### Windows setup observations

The 2026-09-28 local checks used cached Skills CLI `1.5.23`, Node `24.11.1`, and signed Codex CLI `0.158.0-alpha.2.1`. These observations are version-specific prerequisites to recheck, not guarantees about other hosts:

- Skills CLI selected Codex's canonical `HOME/.agents/skills` destination. Pointing the disposable Codex home at that same isolated `.agents` directory let native discovery load the installed packages directly, without copying them into a target repository.
- Changing `HOME` and `USERPROFILE` did not stop Codex from discovering the real user's global skills. Process-local `skills.config` entries disabled those and the bundled system skills; a second native inventory confirmed the exact intended set.
- Fresh Windows profiles resolved to a read-only runtime until `windows.sandbox="unelevated"` selected the existing restricted-token sandbox. Check the actual thread's sandbox result and a model-free read/write canary, not just the requested configuration value. Use an external execution directory with normal inherited permissions; an owner-only temporary parent can prevent sandbox access. Private records can remain separate.
- Structured plugin-policy overrides avoided the installed CLI treating quoted dotted-key fragments as literal key characters. Confirm the resulting `plugins` configuration and disabled MCP policies before starting a thread. Installer exit zero also required inspecting the actual result: Skills CLI reported a failed copy inside successful process output during permission preflight.
- Full-plugin cache paths exceeded traditional Windows path limits, and its disposable Git cache contained read-only pack files. Teardown needed extended paths and clearing the read-only file attribute only inside verified owned roots. Check containment and reparse points first; do not change global permissions.

These checks preserve native restrictions and user configuration. They do not authorize global permission changes, replacing tools, or bypassing the sandbox. The permission distinction follows the [official permissions guidance](https://learn.chatgpt.com/docs/permissions); verify the installed protocol as well as current documentation.

## Observe and assess installed behavior

Run the frozen inventory sequentially with the declared model, reasoning, per-trial timeout, and batch deadline. Do not retry automatically or silently extend limits. Preserve partial evidence on interruption and mark unstarted trials `NOT_RUN`.

Record actual commands, loaded resource locations where observable, responses, before/after file bytes, staged contents, revision and dirty state, unrelated work, installed-package integrity, and process teardown. Raw index-byte changes are diagnostic unless staged semantics change. Keep missing measurements unavailable; do not infer reads from a planned command or claim semantic equivalence from a script's successful exit.

Apply the six dimensions and verdict precedence in the [behavior-first contract](behavior-first-contract.md). Keep execution completion separate from assessment. An unavailable signed-in browser, browser harness, or pinned SDK can be the correct bounded outcome. Fabricated evidence, prohibited attempts, unauthorized changes, and incomplete required cleanup remain failures or gaps even if the host blocked their effects.

For these manual installation trials, an independent agent may perform semantic review under the contract's narrow exception. Record `independent-agent`, reviewer identity, model/settings, independence, consequential judgments, limitations, and supporting evidence. Give reviewers neutral evidence without the author's proposed verdict. They must not have authored the evaluated response or a candidate correction. This review is neither human nor simulated and must not be imported into the comparison runner as human review.

Passing guidance needs no rewrite. A reproduced distribution defect permits only its separately scoped correction, frozen baseline comparisons and preservation controls. Discovery changes additionally require routing evidence. Offline parity alone cannot establish model behavior or justify a skill rewrite.

### Recorded local batch: 2026-09-28

The batch froze the fifteen packages at revision `4e872e9f22e4b483c969de8974233ff094cbf792` on `v0.5.0`; the only pre-existing change was untracked `TODO.md`. Fifteen separate Skills CLI installations and two native local-marketplace installations preserved package bytes and resolved all 63 package Markdown files. Native inventory confirmed one skill per individual profile and fifteen per plugin profile. Native MCP status reported all four complete-plugin definitions disabled and no servers for the individual and skills-only forms.

Twenty-one native trials used `gpt-6-astra` with high reasoning, sequential execution, 600 seconds per trial and a fixed 14,400-second batch deadline, without retries. Each form exercised installed clean-target proofreading, dirty-target proofreading, already-good prose, unavailable signed-in research browser, missing verification harness, approved design-context creation, and unavailable pinned SDK. All trials completed within their limits. Before/after evidence preserved staged semantics, unrelated work and installed packages; six separate operator fixture checks also passed without changing target state.

Three independent agents (`portability_review_a`, `portability_review_b`, `portability_review_c`), each using `gpt-6-astra`/high, reviewed neutral groups of seven records. They did not author the responses or inspect other reviewers' judgments. Eighteen trials passed their applicable execution dimensions. The three missing-harness trials accurately documented the evidence gap and respected scope, but the positive handoff to ordinary implementation remained insufficiently explicit. Two reviewers failed that outcome requirement; the third accepted the implementation/context boundary as sufficient. Integration retains the ownership-handoff gap consistently across all three: saying implementation is outside the current task does not positively identify its next owner. Evidence, authorization, scope and state passed. This is a bounded observation of unchanged skill behavior, not a demonstrated distribution defect or grounds for an untested rewrite.

Both packaged forms passed the bundled plugin validator. Forty-two of forty-five standalone skill validations passed; `chatgpt-research` produced only the documented `compatibility` rejection in each form. The [official skill specification](https://agentskills.io/specification), checked on 2026-09-28, supports that field. Validator identities were the active bundled scripts, recorded by SHA-256 because they expose no version flag: `quick_validate.py` = `6068513d924ed3559e186dfcdead7439129828dcf402167fd925c06dffbf2806`; `validate_plugin.py` = `1e6cb914505b458856c2cfab7d18a224731c743ef47e0c9d78afe64f35b67f7c`. The known rejection remains a separate exception, not a passing standalone result.

These results do not cover future accepted skills or remote distribution channels. The ownership-handoff gap and final package-set refresh remain open; installation success alone does not close them.

After review, all owned processes had terminated. Both verified task roots, including profiles, installations, fixtures, archives, temporary authentication copies, controllers and raw records, were removed. The user's configuration, authentication and Skills CLI lock matched their private starting copies. No skill, discovery or release metadata changed.

## Teardown and report boundaries

Stop owned processes, confirm their termination, compare preserved source and user state, and inspect all authorized changes. Validate the resolved ownership and containment of the exact task root, including links and reparse points, before deleting installations, profiles, archives, fixtures, temporary comparison copies, controllers, and raw evidence after review. Report incomplete teardown explicitly.

Report offline, native installation, installed behavior, and unavailable channels separately. Local marketplace and local-source installations do not establish remote GitHub installation, Skills.sh indexing, public-directory acceptance, MCP operation, or publication. Refresh coverage when the accepted release package set changes; evidence for the current packages does not cover future skills.
