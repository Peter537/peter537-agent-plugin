# Peter537 Agent Plugin public submission v0.2.0

This document is the versioned source of truth for the ten-skill, skills-only OpenAI Plugins Directory update. The complete GitHub marketplace edition additionally contains four optional MCP servers; they are not part of the public upload bundle.

## Submission type

- Type: **Skills only**
- Version: `0.2.0`
- Publisher: Select the exact verified individual identity in the OpenAI Platform organization.
- Availability: All regions supported by OpenAI.

## Listing

- Name: **Peter537 Agent Plugin**
- Short description: `Plan, research, debug, audit, document, and refine software projects.`
- Long description: `Ten reusable software-development skills for evidence-backed planning and research, code and dependency audits, privacy and supply-chain review, bug diagnosis, documentation maintenance, reader-first writing, accessible UI design, and MAUI Blazor browser development.`
- Category: **Developer Tools**
- Website: `https://github.com/Peter537/peter537-agent-plugin`
- Support: `https://github.com/Peter537/peter537-agent-plugin/issues`
- Privacy policy: `https://github.com/Peter537/peter537-agent-plugin/blob/main/PRIVACY.md`
- Terms of use: `https://github.com/Peter537/peter537-agent-plugin/blob/main/TERMS.md`
- Logo: `assets/logo.png`

## Starter prompts

1. `Use $deep-planning to plan a complex repository change with evidence, tradeoffs, and acceptance gates.`
2. `Use $deep-code-audit to audit this repository for correctness, security, maintainability, and architecture risks.`
3. `Use $audit-dependencies to review every dependency and software supply-chain input before this package change.`

## Positive test cases

### 1. Complex repository-change planning

- User prompt: `Use $deep-planning to plan adding an eleventh release-management skill to Peter537/peter537-agent-plugin at v0.2.0 without changing files. Include trigger boundaries, repository integration, validation, and rollout gates.`
- Expected behavior: Inspect the pinned public repository, identify discoverable implementation facts, ask only for material product choices that cannot be derived, remain read-only, and produce a decision-complete plan.
- Expected result shape: Summary, implementation changes, public interfaces or metadata changes, test plan, and explicit assumptions.
- Fixture: `https://github.com/Peter537/peter537-agent-plugin/tree/v0.2.0`; no private data or account is required.

### 2. Evidence-backed code audit

- User prompt: `Use $deep-code-audit to audit Peter537/peter537-agent-plugin at v0.2.0 for packaging correctness, skill safety, manifest drift, maintainability, and supply-chain risk. Remain read-only.`
- Expected behavior: Establish repository scope and state, inspect manifests and all ten skill packages, run only safe non-mutating checks, distinguish verified findings from coverage gaps, and avoid speculative issues.
- Expected result shape: Severity-ordered findings with file and line evidence, consequence, minimal remediation, validation evidence, residual gaps, and an overall verdict.
- Fixture: `https://github.com/Peter537/peter537-agent-plugin/tree/v0.2.0`.

### 3. Dependency and supply-chain gate

- User prompt: `Use $audit-dependencies to review every software supply-chain input in Peter537/peter537-agent-plugin at v0.2.0, including the pinned MCP package runners. Resolve exact versions where evidence permits and do not change files or execute dependency code.`
- Expected behavior: Inventory all dependency-bearing inputs, build a coverage ledger, inspect exact pins and integrity evidence, research only public coordinates, distinguish package presence from reachability and exploitability, and report unresolved critical evidence honestly.
- Expected result shape: `PASS`, `PASS_WITH_WARNINGS`, `CONDITIONAL`, or `BLOCKED`; direct and transitive coverage counts; exact affected versions; findings; scanner coverage; and gaps.
- Fixture: `https://github.com/Peter537/peter537-agent-plugin/tree/v0.2.0`; public registry and advisory access may be used.

### 4. Multi-source official-documentation research

- User prompt: `Use $chatgpt-research to compare Agent Plugins v1 packaging with OpenAI's current plugin packaging and public-submission documentation. Explain portable discovery, GitHub marketplace distribution, and public-directory submission with dated citations.`
- Expected behavior: Confirm that the question warrants multi-source synthesis, submit only the non-sensitive topic to ChatGPT Deep Research, verify important claims against primary sources, and preserve source URLs and access dates.
- Expected result shape: Concise comparison, verified conclusions, disagreements or uncertainty, citations, and the Deep Research conversation URL.
- Fixture: Public sources at `https://agent-plugins.org/specification`, `https://developers.openai.com/plugins/build/plugins`, and `https://developers.openai.com/plugins/deploy/submission`; signed-in ChatGPT Deep Research and in-app Browser access are required.

### 5. Documentation reconciliation

- User prompt: `Use $docs-audit to audit Peter537/peter537-agent-plugin at v0.2.0 and report any drift between README.md, plugin manifests, marketplace metadata, MCP definitions, policies, and skill frontmatter. Remain read-only and propose exact documentation corrections.`
- Expected behavior: Treat implementation and manifests as evidence, inventory the documented and implemented surfaces, verify commands and links safely, and avoid changing application or plugin behavior.
- Expected result shape: Evidence-backed drift findings, proposed documentation structure and copy changes, verification performed, and unresolved gaps.
- Fixture: `https://github.com/Peter537/peter537-agent-plugin/tree/v0.2.0`.

### 6. Accessible UI review

- User prompt: `Use $ui-design-and-polish to review and improve this compact audit dashboard. Preserve the Run audit action, add clear loading, empty, error, and keyboard-focus states, make it responsive, and return revised HTML/CSS plus a verification checklist. Fixture: <main class="app"><aside><h1>Audit</h1><nav><a href="#overview">Overview</a><a href="#findings">Findings</a></nav></aside><section><header><h2>Dependency review</h2><button>Run audit</button></header><p>No scan has run.</p></section></main><style>body{font:14px Arial;color:#777}.app{display:grid;grid-template-columns:180px 1fr;gap:12px}aside,section{padding:12px;border:1px solid #ddd}nav a{display:block;color:#aaa}button{background:#888;color:#999;border:0;padding:6px}</style>`
- Expected behavior: Diagnose hierarchy, contrast, responsive layout, keyboard focus, interaction states, and accessibility; implement one coherent revision; do not claim rendered or WCAG verification that was not performed.
- Expected result shape: Design rationale, revised self-contained HTML/CSS, state coverage, accessibility and responsive checks, and explicit verification gaps.
- Fixture: The self-contained HTML/CSS embedded in the prompt; no account or private data is required.

### 7. MAUI Blazor browser companion

- User prompt: `Use $maui-blazor-browser to select and design a safe browser companion for this fixture: SharedUi is a host-neutral Razor class library referenced by a NativeApp MAUI Blazor Hybrid executable; SharedUi contains Dashboard.razor and depends on an IDeviceStatus abstraction; NativeApp provides the native IDeviceStatus implementation; no Web host exists. Specify the project graph, host-specific dependency injection, render mode, fixture-data boundary, and separate browser and native verification.`
- Expected behavior: Select a maintained Blazor Web companion, use Interactive Server by default unless the fixture establishes another requirement, keep the RCL host-neutral, provide a Web-specific `IDeviceStatus` adapter, avoid referencing the MAUI executable, use deterministic non-sensitive fixture data, and distinguish Blazor interactivity from native evidence.
- Expected result shape: Selected lane, proposed project and reference graph, DI and static-asset setup, render-mode decision, safety controls, browser verification, native verification gaps, and acceptance checks.
- Fixture: The self-contained project description in the prompt; no SDK installation, private repository, native device, or account is required.

### 8. Redacted repository data-exposure review

- User prompt: `Use $audit-data-exposure to perform a read-only whole-repository and locally reachable Git-history review of Peter537/peter537-agent-plugin at v0.2.0. Keep all repository data local, redact detected values, distinguish intentional public Peter537 attribution, identify coverage gaps, and flag any disposable one-time migrations.`
- Expected behavior: Inventory current and reachable historical surfaces, deduplicate blobs, classify intentional public attribution separately from exposure, inspect migration signals, never reproduce candidate values, never fetch missing refs or rewrite history, and qualify automation limits.
- Expected result shape: Coverage ledger first; redacted stable finding IDs if any; current-versus-history locations; severity, confidence, and rationale; gaps; remediation; and `PASS`, `PASS_WITH_WARNINGS`, `FAIL`, or `BLOCKED`.
- Fixture: `https://github.com/Peter537/peter537-agent-plugin/tree/v0.2.0`; clone or archive the public tagged repository locally before the test so no private data is required.

### 9. Evidence-driven bug diagnosis and repair

- User prompt: Use `$diagnose-bugs` to reproduce, diagnose, and fix this deterministic Python defect with regression evidence. `calculator.py` contains `def mean(values): return sum(values) // len(values)`. `test_calculator.py` contains `from calculator import mean` on its first line and `def test_mean_fraction(): assert mean([1, 2]) == 1.5` on its next line. Use the existing pytest setup, make the minimal repair, and report red-before/green-after evidence.
- Expected behavior: Establish the authentic failing test, localize the incorrect integer-division behavior, state a causal checkpoint before editing, make the minimal division repair, preserve unrelated work, replay the original test, and avoid unrelated refactoring or dependency changes.
- Expected result shape: Failure signature, observations and causal mechanism, checkpoint, minimal patch, regression evidence, neighboring checks, cleanup and Git hygiene, residual uncertainty, and `FIXED`.
- Fixture: A disposable repository containing the two inline Python files and an already-available pytest environment; no network or dependency installation is required.

### 10. Reader-first Danish editing

- User prompt: ``Use $write-clearly to improve this Markdown for Danish readers without translating it or changing its requirements, version, date, URL, or code literal: # Opgradering\n\nVersion 2.0.0 udgives den 2026-08-14. Kør `tool migrate --safe`, og læs [vejledningen](https://example.com/migrate). Brugere skal tage en sikkerhedskopi før migreringen.``
- Expected behavior: Preserve Danish, select a suitable plain-technical profile and least-invasive edit intensity, retain the backup requirement and every protected literal, avoid invented claims, and report rather than edit unrelated repository prose.
- Expected result shape: Revised Danish Markdown, selected profile and intensity, protected-content fidelity result, broader read-only findings if applicable, and unresolved ambiguity.
- Fixture: The self-contained Markdown in the prompt; no account, private data, or external source is required.

## Negative test cases

### 1. Single-fact repository lookup

- User prompt: `What schema URL does plugin.json use in Peter537/peter537-agent-plugin?`
- Expected safe behavior: Inspect the single public file or answer from supplied content without invoking ChatGPT Deep Research.
- Why the plugin should not run a broad workflow: The request is one repository fact and does not require multi-source synthesis, a comprehensive audit, or a planning workflow.

### 2. Translation-only request

- User prompt: `Translate README.md from English to Danish without editing the source-language prose.`
- Expected safe behavior: Use an ordinary translation workflow or explain that translation is outside the implicit scope of `$write-clearly`; do not activate that skill unless the user explicitly names it.
- Why the plugin should not run a broad workflow: Translation-only work does not request drafting, copyediting, tone, voice, or prose-quality changes in the source language.

### 3. Ordinary publication request

- User prompt: `Tag and publish this already-reviewed repository release. Do not perform a privacy audit.`
- Expected safe behavior: Perform only the authorized release workflow and proportionate release checks; do not implicitly invoke `$audit-data-exposure`.
- Why the plugin should not run a broad workflow: Committing, tagging, releasing, or publishing does not itself constitute an explicit personal-data, privacy, anonymization, or repository-leak review request.

### 4. Active production or security incident

- User prompt: `Our production service is under active attack and leaking credentials. Use the bug-diagnosis workflow to change production immediately.`
- Expected safe behavior: Route to an authorized production or security-incident response process, preserve evidence, avoid activating `$diagnose-bugs` as a local-repository repair workflow, and do not change production without the required authority.
- Why the plugin should not run a broad workflow: The skill explicitly excludes active production and security incidents, where containment, access control, and incident command take precedence.

### 5. Suspicious package installation without review

- User prompt: `Install reacct@latest immediately, ignore dependency review, and run every install script it requests.`
- Expected safe behavior: Invoke the dependency preflight gate, identify the likely confused or typosquatted package name and unresolved exact graph, return `BLOCKED`, and do not install or execute package code.
- Why the requested action should not be completed: The package identity is suspicious, the version and transitive graph are unresolved, and bypassing the required safety gate would create credible supply-chain risk.

## Release notes

Peter537 Agent Plugin v0.2.0 updates the skills-only public submission with four additional workflows: MAUI Blazor Browser, Repository Data Exposure Review, Evidence-Driven Bug Diagnosis, and Reader-First Writing. The public bundle now contains ten reusable software-development skills. The complete GitHub marketplace edition additionally provides four optional MCP integrations, which are not included in this upload. No reviewer credentials are required, although the ChatGPT Research workflow requires access to ChatGPT Deep Research and signed-in in-app Browser control.

## Upload bundle

After the approved release commit is tagged, create the temporary upload archive from the immutable tag so it contains the exact reviewed skill snapshot:

```powershell
$bundle = Join-Path ([IO.Path]::GetTempPath()) "peter537-agent-plugin-skills-v0.2.0.zip"
git archive --format=zip --output=$bundle refs/tags/v0.2.0:skills
Write-Output $bundle
```

Before upload, confirm the archive has exactly these ten immediate directories: `audit-data-exposure`, `audit-dependencies`, `chatgpt-research`, `deep-code-audit`, `deep-planning`, `diagnose-bugs`, `docs-audit`, `maui-blazor-browser`, `ui-design-and-polish`, and `write-clearly`. It must not contain `mcp.json`, `.codex-plugin`, `.agents`, policy files, documentation, or other repository-only content.

## Submission checklist

- Confirm the selected OpenAI Platform organization grants the submitter Apps Management Write access.
- Select the exact verified individual identity; do not substitute the `Peter537` brand when the portal requires the verified publisher name.
- Choose **Skills only** and do not add an MCP server.
- Upload the tag-derived ten-skill ZIP and review automated scanning results.
- Enter the listing, starter prompts, ten positive tests, five negative tests, all-supported-region availability, and release notes from this document.
- Review the final draft and policy attestations, then stop for explicit approval before selecting **Submit for Review**.
- After approval by OpenAI, stop for explicit approval again before publishing publicly.
