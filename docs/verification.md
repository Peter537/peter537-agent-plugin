# Repository Verification Map

This is the canonical maintainer map for choosing verification evidence in Peter537 Agent Plugin. It routes a changed repository surface to existing checks; it is not a validator, an eval runner, or a substitute for domain judgment.

The evidence boundaries follow OpenAI's current guidance for [skill packaging](https://developers.openai.com/plugins/build/skills), [plugin packaging](https://developers.openai.com/plugins/build/plugins), [installed-plugin testing](https://developers.openai.com/plugins/deploy/connect-chatgpt), and [submission validation](https://developers.openai.com/plugins/deploy/submission-errors). Packaging, installed behavior, live services, and public-directory review remain separate evidence layers.

## How to use this map

1. Record the starting branch, commit, and complete Git state before changing files.
2. Run `OFFLINE-01`, then identify every changed surface in the routing table and run any additional `always` and `when-changed` rows that the aggregate command does not cover.
3. Run `release` rows only during an authorized release workflow. Run `conditional` or `optional` rows only when their prerequisites and authorization are present.
4. Record each selected row as `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`. A missing prerequisite is `BLOCKED`, not a pass or a repository defect.
5. Remove task-created outputs and stop task-created processes. Compare the final Git state with the starting state and explain every remaining change.

Use `python` from the active repository environment. On Windows, `python` and `python3` can resolve to different installations; record the interpreter and validator versions when that distinction affects results. Commands using `<active-skill-creator>` or `<active-plugin-creator>` refer to the corresponding bundled skill directory in the current Codex installation. Do not copy a user-specific absolute path into repository documentation.

## Evidence vocabulary

| Field | Values | Meaning |
| --- | --- | --- |
| Evidence class | `static-offline` | Parses or inspects repository content without running the represented product behavior. |
| Evidence class | `isolated-fixture` | Creates or checks disposable local fixtures outside this repository. |
| Evidence class | `model-behavior` | Exercises a skill or routing prompt with a controlled agent comparison. |
| Evidence class | `local-runtime` | Runs an already-available local application, test, or protocol path. |
| Evidence class | `authorized-live` | Uses a browser, public network, external service, account, or third-party executable after separate authorization. |
| Evidence class | `release-external` | Changes or verifies Git refs, installed marketplaces, submission drafts, review state, or publication state. |
| Gate | `always` | Run for every repository change. |
| Gate | `when-changed` | Run when the named surface or its contract changes. |
| Gate | `release` | Run for an authorized release candidate. |
| Gate | `conditional` | Run when the relevant runtime and safe evidence path already exist. |
| Gate | `optional` | Additional live confidence that is not part of the deterministic offline baseline. |

No evidence class substitutes for another. In particular:

- Fixture materialization does not prove that an agent follows the skill.
- An authored verification-context artifact records repository guidance; it does not prove that a documented command ran or that acceptance criteria passed.
- An authored product design-context artifact records source authority, durable decisions, scoped exceptions, and unresolved choices; it does not approve itself or prove rendered UI, runtime behavior, accessibility, or acceptance.
- A static manifest pass does not prove installed discovery, activation, or runtime behavior.
- `tools/list` proves only that a connection advertises tools, not that every tool is correct or safe.
- A rendered DOM or screenshot does not prove Blazor interactivity, native MAUI behavior, complete accessibility, or release packaging.
- Scanner output contains candidates and coverage gaps; a clean scan does not prove anonymization, dependency safety, or absence of sensitive data.
- A valid archive, pushed tag, or successful installation does not prove Skills.sh ingestion, OpenAI review acceptance, or public publication.

### Product evidence layers

These layers describe what a product observation can support; they do not replace the execution classes or authorization gates above.

| Layer | Directly supports | Does not establish by itself |
| --- | --- | --- |
| Static | Source, configuration, schema, and artifact identity at the inspected revision. | Compilation, execution, user-visible behavior, or persistence. |
| Build | Successful production of the named artifact from the recorded inputs. | Correct tests, runtime behavior, or deployment identity. |
| Test | The behavior exercised by the named test at the recorded revision and environment. | Unexercised workflows, production conditions, or broad absence of regressions. |
| API | The observed request, response, authorization, and protocol behavior for the exercised path. | UI interaction, durable state, downstream side effects, or native behavior. |
| UI | The rendered state and interactions actually exercised in the named client and viewport. | Persistence, other clients, backend correctness beyond the observed workflow, accessibility conformance, or native-host behavior. |
| Persistence | The observed state transition across the required reload, reconnect, restart, or storage boundary. | Unrelated data paths, migrations over other datasets, or operational durability outside the fixture. |
| Operational | The observed process, listener, lifecycle, resource, and cleanup behavior in the exercised environment. | Equivalent behavior in production, other deployment variants, or functional correctness outside the observation. |
| Telemetry | Correlated traces, metrics, and logs emitted by the exact exercised run. | Behavior that was not instrumented or observed, root cause, or absence of hidden failure. |
| Native | Behavior exercised in the required native host, operating system, device, lifecycle, or packaging path. | Other native platforms, browser parity, or untested release configurations. |

Choose the cheapest combination that fully supports each acceptance claim. Record unexercised required layers as `BLOCKED`; capture evidence before cleanup, then verify that task-created processes, listeners, fixtures, and writable state are restored.

## Repository baseline and closure

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `BASE-01` | Entire worktree; task owner | Start of every task; `always` | `static-offline` | Run `git status --short --branch` and `git rev-parse HEAD`. Record the branch, commit, staged, unstaged, and untracked state before editing. | None. | Whether existing changes are correct or belong to the current task. |
| `OFFLINE-01` | Repository-owned source, metadata, documentation, eval structure, maintenance tests, and distributed-script tests; repository-maintenance owner | Before handoff; `always` | `static-offline` and `isolated-fixture` | Run `python -B evals/run_offline_checks.py`. Exit `0` means every required bounded check passed and the Git-visible file hashes, status, and path inventory remained unchanged; exit `1` identifies completed-check failures or mutation; exit `2` identifies an infrastructure block. The command aggregates JSON, bounded YAML/frontmatter, Python, and local Markdown-link inspection, development layout validation, common eval-manifest validation, every suite materializer `--list` interface, root maintenance tests, and distributed-script tests. | Unit tests may create disposable repositories in writable OS temporary storage and must clean them. The runner writes nothing intentionally to this repository and reports any state drift without removing it. | Strict grouping, bundled skill or plugin validation, full schemas or semantic truth, model behavior, runtime or live evidence, MCP behavior, installation, release state, or publication. |
| `BASE-02` | Changed tracked text; task owner | Before handoff; `always` | `static-offline` | Run `git diff --check`. Exit `0` means Git found no whitespace errors in tracked diffs. | None. | Content correctness, untracked files, generated artifacts, or complete formatting validity. |
| `BASE-03` | Entire worktree; task owner | Before handoff; `always` | `static-offline` | Run `git status --short --branch`, review the complete diff, and compare both with `BASE-01`. Every remaining path must be authorized and every unrelated path must retain its starting state. | Remove task-created backups, fixture outputs, caches, logs, and probes first. | Runtime behavior, remote Git state, or publication state. |

## Retrospectives and rule incubation

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `RETRO-01` | [`docs/retrospective-and-rule-incubation.md`](retrospective-and-rule-incubation.md) and any proposed destination artifact; retrospective owner | Retrospective-process changes or any recurring observation generalized into repository behavior; `when-changed` | `static-offline`, plus the evidence class required by the selected destination | Complete the worksheet outside the repository, minimize and sanitize its evidence, select one primary disposition, record authority and evidence limits, exercise the applicable positive and allowed-behavior controls, and run the destination-specific verification rows. For a deterministic rule, require must-detect, must-allow, exception, redaction, and non-mutation tests plus reviewed warning-only evidence before separately approving blocking behavior. | Keep task-created source packets, completed worksheets, canaries, captures, reviewer output, and reports temporary and untracked. Delete only those task-created local copies after capturing the sanitized decision; preserve user-provided or pre-existing evidence unless separately authorized, report external retention that cannot be controlled, and confirm the final state through `BASE-03`. | Faithful human sanitization, universal absence of sensitive data, genuine recurrence, correctness of the selected disposition, future false-positive rates, or validity beyond the observed scope. |

## Repository verification context

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `CONTEXT-01` | A repository-owned verification artifact and any separately authorized dependency-free thin wrapper created or maintained through `$verification-context`; context owner | Approved context or wrapper creation or change; `when-changed` | `static-offline`, and `local-runtime` only for safely exercised repository-native commands | Confirm every exact authorized path; the artifact's owner, audience, scope, acceptance authorities, target variants, direct commands and working directories, prerequisites, side effects, persistence boundaries, reset procedures, cleanup ownership, evidence limits, and `verified-current`, `discovered-unverified`, `stale`, or `blocked` states; and that any wrapper only sequences already-authoritative commands and propagates failure. Reconcile cleanup prose with executable behavior. Record a last-verified revision only for a command actually exercised against that target. | Context and wrapper edits are persistent. Any exercised command keeps its own documented effects and cleanup boundary; do not install tooling, create a harness, add assertions or retries, or run a command whose complete cleanup target is not task-owned. | That a documented command ran on another revision, that a wrapper adds verification coverage, that acceptance criteria pass, implicit skill activation, runtime behavior not exercised during maintenance, or release readiness. |

## Product design context

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `DESIGN-CONTEXT-01` | A repository-owned persistent project design-context artifact created or maintained through `ui-design-and-polish`; design-context owner | Directly requested context creation or maintenance at an existing authoritative or exact approved path; `when-changed` | `static-offline` | Confirm the authorized path, source authority and provenance, applicable scope and product or platform variants, approved decisions, observed facts, provisional synthesis, unresolved choices, valid historical rationale, scoped exceptions, locale and accessibility constraints, canonical token identifiers without copied mutable values, component interfaces without copied implementation details, bounded exemplar provenance and non-copy limits, local links, protected files, and final Git state. | The context edit is persistent; inspection and repository-native static checks remain read-only and must preserve unrelated staged, unstaged, and untracked work. | Human approval, current truth beyond the inspected revision, implicit activation, rendered hierarchy, UI interaction, runtime behavior, accessibility conformance, acceptance, or release readiness. |

## Skills, layout, grouping, and catalog

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `LAYOUT-01` | `skills/`, `evals/`, `skills.sh.json`, `docs/skills/README.md`, and `.codex-plugin/plugin.json`; repository layout owner | Any listed path changes; `when-changed` | `static-offline` | Run `python -B evals/validate_repository_layout.py`. Exit `0` proves the current flat layout, skill/eval pairing, frontmatter-directory names, grouping references, catalog pairs, and canonical `./skills/` discovery satisfy the repository-owned development contract. `OFFLINE-01` includes this development-mode check. | None; `-B` suppresses Python bytecode caches. | Full skill, eval, Skills.sh, plugin, or Markdown schemas; behavior or release readiness. |
| `LAYOUT-02` | Same surfaces; release owner | New skill, grouping, catalog, or release preparation; `release` | `static-offline` | Run `python -B evals/validate_repository_layout.py --strict-groups`. Exit `0` additionally proves every discovered skill is assigned to one current group. | None. | Skills.sh ingestion, page rendering, or its complete external schema. |
| `LAYOUT-03` | `evals/validate_repository_layout.py` or its tests; layout validator owner | Validator behavior changes and at release; `when-changed` | `isolated-fixture` | Run `python -B -m unittest evals/test_repository_layout.py -v`. Require all tests to pass; permission or link-support limitations are reported as `BLOCKED` or explicit skips. `OFFLINE-01` includes this root maintenance-test module. | Creates and removes synthetic repositories under the OS temporary directory. A writable temporary location is required. | The real repository's current layout; run `LAYOUT-01` separately. |
| `SKILL-01` | One `skills/<slug>/SKILL.md`; skill package owner | Skill instructions or frontmatter change; `when-changed` | `static-offline` | Run `python -B <active-skill-creator>/scripts/quick_validate.py skills/<slug>`. Exit `0` is the expected result except for the documented `chatgpt-research` disagreement below. | Requires the active bundled validator and PyYAML; no repository writes. | `agents/openai.yaml`, references, scripts, links, trigger quality, or runtime behavior. |
| `SKILL-02` | All skill packages; release owner | Release preparation; `release` | `static-offline` | Run `SKILL-01` for every immediate skill directory and retain per-skill results. Any new diagnostic blocks the release. | Same as `SKILL-01`. | Complete plugin packaging or behavior across models and contexts. |
| `SKILL-03` | `skills/<slug>/agents/openai.yaml`, references, scripts, and other supporting files; skill package owner | Any supporting resource changes; `when-changed` | `static-offline` | Run `OFFLINE-01` for bounded YAML/frontmatter parsing, Python compilation, and local Markdown-link checks. Also run `PLUGIN-01`, resolve every local resource named by `SKILL.md`, and confirm every file remains inside the skill package. No repository-owned command performs full YAML or complete semantic reference validation. | Parser caches are not permitted in the repository; use `python -B` for Python checks. | Whether a model loads the right reference at the right time or follows its guidance. |

### Current standalone-validator disagreement

The current bundled standalone skill validator exits `1` for `skills/chatgpt-research/` because it rejects the `compatibility` frontmatter field. This is a validator/specification disagreement, not a passing result and not a general warning allowance. Classify it separately only when all of the following are true:

- the diagnostic is exactly the known `compatibility`-field rejection and contains no additional error;
- current official skill guidance still supports the field;
- `PLUGIN-01` passes; and
- the exception and validator version are recorded in the verification report.

Any changed diagnostic or additional failure blocks completion.

## Eval manifests, fixtures, and model behavior

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `EVAL-01` | [`evals/behavior-first-contract.md`](../evals/behavior-first-contract.md), `evals/<slug>/cases.json`, `evals/routing-matrix.json`, and materializer inputs; eval-suite owner | Evaluation policy, manifest, routing, or fixture changes; `when-changed` | `static-offline` | First run `python -B evals/validate_eval_manifests.py`. Require canonical trigger owners, strict routing-versus-execution fields, unique behavioral false-positive references, noncontradictory normalized signals, complete invocation pairs, valid reciprocal boundaries, and resolved coverage references. Then, when the suite provides a materializer, run `python -B evals/<slug>/materialize_fixtures.py --list`; for `chatgpt-research`, run `python -B evals/chatgpt-research/materialize_packets.py --list`. Require exit `0` from both applicable checks. `OFFLINE-01` aggregates these commands in deterministic suite order. | None. Fourteen suites have materializers: thirteen create Git fixtures and `chatgpt-research` creates packets; `write-clearly` instead uses `SCRIPT-01`. | Semantic case quality, actual activation, execution, progressive disclosure, fixture execution, or the safety of scripts named by verification commands. Structural validation does not authorize command execution. |
| `EVAL-02` | Materializer code and repository-oriented fixtures; eval-suite owner | Materializer or fixture changes; `when-changed` | `isolated-fixture` | Run the relevant materializer with `--all --output <empty-external-directory>`. Require successful creation and the suite-declared Git and privacy invariants. The destination must be new or empty and outside this repository. | Thirteen suites create disposable Git repositories; `chatgpt-research` creates packets. Output intentionally remains for inspection. Delete only the exact validated output directory after capturing evidence. | Model behavior, routing, or correctness of repository-native commands inside each fixture. |
| `EVAL-03` | One selected case; eval-suite owner | Focused investigation; `conditional` | `isolated-fixture` | Run the materializer with `--case <id> --output <empty-external-directory>`, then run only the declared repository-native commands that are safe and available. | Python may create `__pycache__`; .NET may create `bin/` and `obj/` inside the disposable repository. Remove the complete disposable repository afterward. | Untested variants, unavailable runtimes, or skill behavior. Do not restore packages or install workloads implicitly. |
| `EVAL-04` | `cases.json`, `routing-matrix.json`, `SKILL.md`, trigger metadata, or the [behavior-first contract](../evals/behavior-first-contract.md); skill/eval owner | Skill behavior, routing, or grading-policy changes; `when-changed` | `model-behavior` | Compare baseline and candidate with the same model, reasoning effort, prompt, fixture, tools, limits, environment, and authorization. Run trigger activation and ownership separately from behavioral execution. Grade activation and owner, observable outcome, claim support, authorization and safety, scope and necessity, and final-state integrity independently as `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`; classify consequential claims as `supported`, `bounded`, `unresolved`, or `unsupported`. For completed-change claims, grade the applicable static, build, test, API, UI, persistence, operational, telemetry, and native layers independently and do not substitute one layer for another. For authorized mutations, capture comparable before-and-after evidence; run the suite's indexed false-positive controls. Grade prose, plans, screenshots, tool order, and implementation shape semantically, reserving exact matching for stable machine contracts, protected literals, exit codes, archive membership, and repository-state invariants. For routing, derive the prompt set from the matrix, hide expected owners from test agents, and run three identical independent passes. When `allow_implicit_invocation` is `false`, exercise an explicit invocation and a semantically matching uninvoked near miss, and require activation only for the explicit case. For `$verification-context`, grade the authored guidance separately from evidence that its documented commands ran. No tracked generic runner currently exists; `TODO-006` owns future harness work. | Keep transcripts, reports, screenshots, URLs, and run outputs temporary and untracked; remove them after review. | Universal behavior, stable routing across every model/context, unexercised evidence layers, native host internals, or publication review acceptance. |

## Distributed scripts and deterministic tests

These four suites currently provide standard-library automated tests:

```text
python -B -m unittest discover -s evals/audit-data-exposure/tests -v
python -B -m unittest discover -s evals/audit-dependencies/tests -v
python -B -m unittest discover -s evals/chatgpt-research/tests -v
python -B -m unittest discover -s evals/write-clearly/tests -v
```

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `SCRIPT-01` | The three distributed Python scripts and the four suites above; script owner | Relevant script, fixture, or contract changes; `when-changed`; all four at `release` | `isolated-fixture` | Run the applicable command above and require the complete suite to pass. `OFFLINE-01` discovers and runs all four suites. A writable OS temporary directory is a prerequisite. | Tests create temporary files and Git repositories and clean them on success. Report cleanup failures and remove only positively identified test output. | Detector completeness, semantic equivalence, anonymization, research truth, or vulnerability absence. |
| `SCRIPT-02` | `scan_repository_data_exposure.py`; data-exposure owner | Scanner behavior changes or an explicitly requested privacy review; `conditional` | `static-offline` | Use the scope and arguments documented by `$audit-data-exposure`. Exit `0` may still include candidates or coverage gaps; exit `2` is an inspection failure. | Read-only Git and filesystem inspection; no network or repository writes. | A clean repository, legal compliance, or proof that no personal data exists. |
| `SCRIPT-03` | `inventory_dependency_files.py`; dependency-audit owner | Inventory behavior changes or dependency-surface review; `conditional` | `static-offline` | Run `python -B skills/audit-dependencies/scripts/inventory_dependency_files.py . --format json`. Exit `0` can include gaps; exit `2` means the root was unsafe or unavailable. | Read-only filesystem and Git metadata; does not execute dependency code or use the network. | Resolution, vulnerabilities, provenance, reachability, or package safety. |
| `SCRIPT-04` | `check_prose_fidelity.py`; writing owner | Supported prose edits or checker changes; `conditional` | `static-offline` | For a clean tracked target, run `python -B skills/write-clearly/scripts/check_prose_fidelity.py --git-base HEAD --path <path>`. For pre-existing work, use an external pre-task copy with `--before` and `--after`. Exit `0` means no protected-literal difference, `1` requires editorial review, and `2` is an inspection failure. | Pair mode creates a private external baseline that must be removed after verification. | Semantic equivalence, factual truth, voice, clarity, or reader comprehension. |

## Plugin, marketplace, documentation, and assets

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `PLUGIN-01` | `.codex-plugin/plugin.json`, all skills, `agents/openai.yaml`, and referenced UI assets; Codex package owner | Any listed path changes; `when-changed`; always at `release` | `static-offline` | Run `python -B <active-plugin-creator>/scripts/validate_plugin.py .`. Exit `0` proves the bundled validator accepts the Codex manifest, interface, skill metadata, agent UI metadata, and referenced assets. | Requires the active bundled validator and PyYAML; no repository writes. | Root `plugin.json`, `mcp.json`, marketplace metadata, Skills.sh, README parity, external schemas, installation, activation, or runtime behavior. |
| `PORTABLE-01` | `plugin.json`; portable package owner | Portable metadata changes; `when-changed`; always at `release` | `static-offline` | Parse it as JSON and compare name, version, description, author, license, repository, and keywords with the Codex manifest and release intent. Its remote schema is the authority, but no repository-owned full local schema command exists. Record external-schema validation as a separate live or unavailable result. | Local parsing is read-only. Fetching the schema requires separately authorized network access and may use a cache. | Client compatibility, discovery, or support for every Agent Plugins v1 component. |
| `MARKET-01` | `.agents/plugins/marketplace.json`; marketplace owner | Marketplace metadata changes; `when-changed`; always at `release` | `static-offline` | Parse it as JSON and verify the marketplace name, plugin name, `./` source resolution, installation/authentication policy, and category against the Codex manifest and README. No repository-owned marketplace validator exists. | None. | A successful local or GitHub marketplace installation. |
| `MARKET-02` | Local marketplace source and current worktree; installation owner | Marketplace metadata changes; `conditional` | `local-runtime` | Add the repository's local marketplace source in an isolated Codex profile, install the plugin, start a new task, and verify the expected skills and MCP definitions are discovered separately. | Mutates the isolated Codex marketplace configuration and plugin cache. Remove the test profile or restore its recorded starting state. | Tagged GitHub installation, remote availability, public-directory publication, or Skills.sh ingestion. |
| `GROUP-01` | `skills.sh.json`; Skills.sh grouping owner | Grouping changes; `when-changed`; always at `release` | `static-offline` | Run `LAYOUT-01` and `LAYOUT-02`. They prove repository grouping invariants, not the complete remote schema. Record official-schema validation separately when network access is authorized. | Offline checks are read-only; external validation may use network caches. | Skills.sh catalog ingestion, badge availability, page contents, or security results. |
| `DOC-01` | Root `AGENTS.md`, README, policies, support, terms, license, skill catalog, eval guide, and maintainer documentation; documentation owner | Any listed prose or link changes; `when-changed` | `static-offline` | Run `OFFLINE-01` for bounded repository-local Markdown links, images, reference definitions, and heading fragments. Review changed prose separately and verify factual claims against manifests, skills, MCP definitions, and release state. | Read-only. The offline checker never visits external links merely because source text contains them. | Complete Markdown semantics, external reachability, policy suitability, legal compliance, factual truth, prose quality outside the reviewed scope, or whether a Codex client loaded or followed `AGENTS.md`. |
| `DOC-02` | External policy, support, website, badge, and documentation URLs; channel owner | URL changes and release preparation; `optional` | `authorized-live` | Open the exact public HTTPS URLs and record status, destination, and access date. Inspect content only to the extent required by the release or channel. | Uses the public network and browser state; keep captures and URLs out of tracked output unless the repository explicitly owns them. | Future availability, legal sufficiency, or marketplace acceptance. |
| `ASSET-01` | `assets/logo.svg`, `assets/logo.png`, and manifest asset paths; branding owner | Asset or path changes; `when-changed`; always at `release` | `static-offline` | Run `PLUGIN-01`, confirm the PNG is a valid square 1024×1024 image, confirm the editable SVG remains square, and visually inspect the PNG at full size and marketplace-thumbnail size on light and dark surfaces. | Image viewers may create temporary thumbnails or caches; keep them outside the repository and remove task-created copies. | Universal rendering across clients or public-directory approval. |

## MCP verification

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `MCP-01` | `mcp.json` and README MCP table; MCP package owner | Server, transport, argument, or documentation changes; `when-changed`; always at `release` | `static-offline` | Parse `mcp.json`, verify the expected server IDs, transport shapes, pinned package inputs, and README parity. Validate against the current remote schema when separately available. The complete bundled plugin validator does not inspect this file, and no repository-owned MCP schema or smoke harness exists. | Offline parsing is read-only. External schema access is authorized-live. | Server startup, protocol negotiation, advertised tools, tool behavior, or dependency safety. |
| `MCP-02` | Each available MCP server; MCP integration owner | MCP changes or GitHub-edition release; `optional` | `authorized-live` | Start one server at a time and complete `tools/list`; when separately authorized, call one safe public operation. Record unavailable runtimes as gaps. Stop each task-started process and confirm its listener or stdio session closes. | Context7 and Microsoft Learn use the network. Playwright's `npx -y` and Web Forager's `uvx` may download packages, execute third-party code, and alter caches. | Correctness of every tool, privacy of every request, all authentication paths, or end-to-end workflows. |

## Portable-client verification

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `PORTABLE-02` | Root Agent Plugins package in a compatible client; portable package owner | Portable manifest or discovery changes; `optional` | `local-runtime` | Install or open a reviewed repository snapshot in an available compatible client and verify root-manifest discovery, immediate skill discovery, and supported MCP discovery separately. Record unsupported client capabilities as gaps rather than failures in unrelated components. | May mutate client configuration and caches. Use an isolated profile or preserve and restore the recorded starting state. | Compatibility with other clients, marketplace ingestion, or correct execution of every skill and MCP tool. |

## Distribution and release verification

| ID | Changed surface and owner | Trigger and gate | Evidence class | Authoritative check and expected evidence | Temporary effects and cleanup | What it cannot prove |
| --- | --- | --- | --- | --- | --- | --- |
| `GITHUB-01` | Complete tagged repository; GitHub marketplace owner | Authorized release candidate; `release` | `release-external` | Verify the release commit is pushed, create an annotated tag only after approval, refresh remote refs, and prove the peeled local and remote tag resolve to the approved commit. Inspect the tag's complete repository contents. | Fetch changes local refs; tagging changes local refs; push and branch deletion change remote state. These require explicit release authorization. | Installation, MCP startup, OpenAI review, Skills.sh ingestion, or a GitHub Release page. |
| `GITHUB-02` | Tagged GitHub marketplace source; installation owner | After the immutable tag exists; `optional` | `release-external` | Add the exact repository and tag as a marketplace source, install Peter537 Agent Plugin, start a new task, and verify skill discovery, MCP discovery, representative prompts, and available `MCP-02` connections separately. | Uses network access and mutates Codex marketplace configuration and plugin caches. Use an isolated profile or preserve and restore prior state. | OpenAI-directory or Skills.sh publication. |
| `SKILLSH-01` | Skill directories and `skills.sh.json`; Skills.sh channel owner | After approved repository publication; `optional` | `authorized-live` | With explicit telemetry authorization, use the audited Skills CLI to list, install one named skill, and install all discovered skills into a disposable external destination. Verify repository and individual-skill pages, search indexing, and displayed security results separately. | May transmit telemetry, use the network, and change CLI caches or the disposable install destination. Remove only the exact disposable installation. | Immediate catalog ingestion, enduring availability, or installation of MCP servers and plugin metadata. |
| `OPENAI-01` | `docs/public-submission-vX.Y.Z.md` and annotated release tag; public-directory owner | Authorized public submission; `release` | `release-external` | Generate the skills-only archive from the immutable tag with `git archive --format=zip --output=<temporary-bundle> refs/tags/vX.Y.Z:skills`. Verify exact immediate skill directories, all referenced skill resources, and exclusion of `evals`, MCP configuration, manifests, marketplace metadata, policies, and repository documentation. | Writes one archive outside the repository. Delete it after upload or when no longer needed. | Portal acceptance, security-review outcome, approval, or publication. |
| `OPENAI-02` | OpenAI portal draft and publisher identity; public-directory owner | After `OPENAI-01`; `release` | `release-external` | Confirm Apps Management Write access and verified publisher identity, upload the bundle, populate the versioned listing, prompts, tests, availability, and release notes, and review the completed draft. Stop before **Submit for Review** without explicit confirmation and stop again before final **Publish** after approval. | Creates external draft and review state and uploads the public skill bundle. | Review approval, publication timing, or continued directory availability. |
| `RELEASE-01` | Current manifests, README installation guidance, new submission document, and historical submission documents; release owner | Authorized release preparation; `release` | `static-offline` | Confirm intended version/count parity, unchanged starter prompts and MCP definitions unless explicitly included, unchanged historical submission files, and a clean reviewed release diff. Run every applicable offline row before commit; use `GITHUB-01` and `OPENAI-01` for tag and archive evidence. | Offline checks may use the temporary effects documented by their own rows; clean them before the release commit. | Remote tag state, archive contents, installation, review acceptance, or public publication. |

## Optional live eval cases

Only five tracked cases currently authorize an opt-in live layer, and each still requires separate approval for the exact input and destination:

- `audit-dependencies/public-coordinate-advisory-smoke`
- `chatgpt-research/live-public-deep-research-smoke`
- `chatgpt-research/live-direct-browser-capture`
- `maui-blazor-browser/safe-loopback-interactivity-smoke`
- `verify-change/safe-loopback-browser-persistence`

Do not track account-specific browser state, conversation URLs, reports, screenshots, local live URLs, private package coordinates, or external-service responses. Stop task-created processes, close task-created listeners, remove disposable outputs, and record any unavailable layer as `BLOCKED` or not run.

## Known verification gaps

The repository intentionally has no claim of complete automation. These gaps remain owned by later roadmap work or explicit external procedures:

- No generic model runner grades behavioral and routing cases.
- `OFFLINE-01` provides bounded JSON, YAML/frontmatter, Python, and local Markdown-link checks, but no repository-owned command fully validates YAML semantics, every skill resource relationship, Agent Plugins manifests, MCP manifests, marketplace metadata, or the Skills.sh schema.
- No repository-owned MCP `tools/list` harness, marketplace installer smoke, Skills.sh ingestion check, portal validator, or release/tag/archive verifier exists.
- Asset-path validation does not replace dimension, format, full-size, and thumbnail inspection.

Start with `OFFLINE-01`, then select the applicable non-aggregated checks individually and report missing evidence without upgrading it to a pass.
