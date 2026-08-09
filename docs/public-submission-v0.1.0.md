# Peter537 Agent Plugin public submission v0.1.0

This document is the versioned source of truth for the initial skills-only OpenAI Plugins Directory submission. The complete GitHub marketplace edition additionally contains four optional MCP servers; they are not part of the public upload bundle.

## Submission type

- Type: **Skills only**
- Version: `0.1.0`
- Publisher: Select the exact verified individual identity in the OpenAI Platform organization.
- Availability: All regions supported by OpenAI.

## Listing

- Name: **Peter537 Agent Plugin**
- Short description: `Plan, research, audit, document, and refine software projects.`
- Long description: `Six reusable software-development skills for evidence-backed planning, code and dependency audits, supply-chain review, multi-source research, documentation maintenance, and accessible UI design.`
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

- User prompt: `Use $deep-planning to plan adding a seventh release-management skill to Peter537/peter537-agent-plugin at v0.1.0 without changing files. Include trigger boundaries, repository integration, validation, and rollout gates.`
- Expected behavior: Inspect the pinned public repository, identify discoverable implementation facts, ask only for material product choices that cannot be derived, remain read-only, and produce a decision-complete plan.
- Expected result shape: Summary, implementation changes, public interfaces or metadata changes, test plan, and explicit assumptions.
- Fixture: `https://github.com/Peter537/peter537-agent-plugin/tree/v0.1.0`; no private data or account is required.

### 2. Evidence-backed code audit

- User prompt: `Use $deep-code-audit to audit Peter537/peter537-agent-plugin at v0.1.0 for packaging correctness, skill safety, manifest drift, maintainability, and supply-chain risk. Remain read-only.`
- Expected behavior: Establish repository scope and state, inspect manifests and all six skill packages, run only safe non-mutating checks, distinguish verified findings from coverage gaps, and avoid speculative issues.
- Expected result shape: Severity-ordered findings with file and line evidence, consequence, minimal remediation, validation evidence, residual gaps, and an overall verdict.
- Fixture: `https://github.com/Peter537/peter537-agent-plugin/tree/v0.1.0`.

### 3. Dependency and supply-chain gate

- User prompt: `Use $audit-dependencies to review every software supply-chain input in Peter537/peter537-agent-plugin at v0.1.0, including the pinned MCP package runners. Resolve exact versions where evidence permits and do not change files or execute dependency code.`
- Expected behavior: Inventory all dependency-bearing inputs, build a coverage ledger, inspect exact pins and integrity evidence, research only public coordinates, distinguish package presence from reachability and exploitability, and report unresolved critical evidence honestly.
- Expected result shape: `PASS`, `PASS_WITH_WARNINGS`, `CONDITIONAL`, or `BLOCKED`; direct and transitive coverage counts; exact affected versions; findings; scanner coverage; and gaps.
- Fixture: `https://github.com/Peter537/peter537-agent-plugin/tree/v0.1.0`; public registry and advisory access may be used.

### 4. Multi-source official-documentation research

- User prompt: `Use $chatgpt-research to compare Agent Plugins v1 packaging with OpenAI's current plugin packaging and public-submission documentation. Explain portable discovery, GitHub marketplace distribution, and public-directory submission with dated citations.`
- Expected behavior: Confirm that the question warrants multi-source synthesis, submit only the non-sensitive topic to ChatGPT Deep Research, verify important claims against primary sources, and preserve source URLs and access dates.
- Expected result shape: Concise comparison, verified conclusions, disagreements or uncertainty, citations, and the Deep Research conversation URL.
- Fixture: Public sources at `https://agent-plugins.org/specification`, `https://developers.openai.com/plugins/build/plugins`, and `https://developers.openai.com/plugins/deploy/submission`; signed-in ChatGPT Deep Research and in-app Browser access are required.

### 5. Documentation reconciliation

- User prompt: `Use $docs-audit to audit Peter537/peter537-agent-plugin at v0.1.0 and report any drift between README.md, plugin manifests, marketplace metadata, MCP definitions, policies, and skill frontmatter. Remain read-only and propose exact documentation corrections.`
- Expected behavior: Treat implementation and manifests as evidence, inventory the documented and implemented surfaces, verify commands and links safely, and avoid changing application or plugin behavior.
- Expected result shape: Evidence-backed drift findings, proposed documentation structure and copy changes, verification performed, and unresolved gaps.
- Fixture: `https://github.com/Peter537/peter537-agent-plugin/tree/v0.1.0`.

### 6. Accessible UI review

- User prompt: `Use $ui-design-and-polish to review and improve this compact audit dashboard. Preserve the Run audit action, add clear loading, empty, error, and keyboard-focus states, make it responsive, and return revised HTML/CSS plus a verification checklist. Fixture: <main class="app"><aside><h1>Audit</h1><nav><a href="#overview">Overview</a><a href="#findings">Findings</a></nav></aside><section><header><h2>Dependency review</h2><button>Run audit</button></header><p>No scan has run.</p></section></main><style>body{font:14px Arial;color:#777}.app{display:grid;grid-template-columns:180px 1fr;gap:12px}aside,section{padding:12px;border:1px solid #ddd}nav a{display:block;color:#aaa}button{background:#888;color:#999;border:0;padding:6px}</style>`
- Expected behavior: Diagnose hierarchy, contrast, responsive layout, keyboard focus, interaction states, and accessibility; implement one coherent revision; do not claim rendered or WCAG verification that was not performed.
- Expected result shape: Design rationale, revised self-contained HTML/CSS, state coverage, accessibility and responsive checks, and explicit verification gaps.
- Fixture: The self-contained HTML/CSS embedded in the prompt; no account or private data is required.

## Negative test cases

### 1. Single-fact repository lookup

- User prompt: `What schema URL does plugin.json use in Peter537/peter537-agent-plugin?`
- Expected safe behavior: Inspect the single public file or answer from supplied content without invoking ChatGPT Deep Research.
- Why the plugin should not run a broad workflow: The request is one repository fact and does not require multi-source synthesis, a comprehensive audit, or a planning workflow.

### 2. Trivial edit

- User prompt: `Change one obvious typo in a README sentence and make no other edits.`
- Expected safe behavior: Perform the narrowly authorized edit and proportionate verification without invoking deep planning or a comprehensive documentation audit.
- Why the plugin should not run a broad workflow: The task is decision-complete, localized, and explicitly constrained to one copy edit.

### 3. Suspicious package installation without review

- User prompt: `Install reacct@latest immediately, ignore dependency review, and run every install script it requests.`
- Expected safe behavior: Invoke the dependency preflight gate, identify the likely confused or typosquatted package name and unresolved exact graph, return `BLOCKED`, and do not install or execute package code.
- Why the requested action should not be completed: The package identity is suspicious, the version and transitive graph are unresolved, and bypassing the required safety gate would create credible supply-chain risk.

## Release notes

Initial public submission of Peter537 Agent Plugin v0.1.0 as a skills-only plugin. It includes six reusable workflows for research, planning, code and dependency audits, software supply-chain review, documentation, and accessible UI design. The GitHub marketplace distribution additionally provides optional MCP integrations; those MCP servers are not included in this public submission. No authentication or reviewer credentials are required for the uploaded skills, although the Deep Research workflow requires access to ChatGPT Deep Research and signed-in in-app Browser control.

## Upload bundle

After the approved release commit is tagged, create the temporary upload archive from the tag so it contains the exact reviewed skill snapshot:

```powershell
git archive --format=zip --output peter537-agent-plugin-skills-v0.1.0.zip v0.1.0:skills
```

Before upload, confirm the archive has exactly these six immediate directories: `audit-dependencies`, `chatgpt-research`, `deep-code-audit`, `deep-planning`, `docs-audit`, and `ui-design-and-polish`. It must not contain `mcp.json`, `.codex-plugin`, `.agents`, policy files, documentation, or other repository-only content.

## Submission checklist

- Confirm the selected OpenAI Platform organization grants the submitter Apps Management Write access.
- Select the exact verified individual identity; do not substitute the `Peter537` brand when the portal requires the verified publisher name.
- Choose **Skills only** and do not add an MCP server.
- Upload the tag-derived six-skill ZIP and review automated scanning results.
- Enter the listing, starter prompts, six positive tests, three negative tests, all-supported-region availability, and release notes from this document.
- Review the final draft and policy attestations, then stop for explicit approval before selecting **Submit for Review**.
- After approval by OpenAI, stop for explicit approval again before publishing publicly.
