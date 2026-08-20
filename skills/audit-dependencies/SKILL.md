---
name: audit-dependencies
description: Audit every software dependency and supply-chain input in a repository, including direct and transitive packages, nested projects and workspaces, build plugins, CI actions, container images, vendored code, submodules, and runtime-loaded extensions. Use for dependency or package reviews; before adding, installing, upgrading, replacing, or removing dependencies; when manifests or lockfiles change; or when checking exact resolved versions, vulnerabilities, provenance, integrity, licenses, malicious packages, dependency confusion, maintainer risk, or supply-chain attacks. Do not use for broad source-code audits unrelated to dependencies.
license: MIT
---

# Dependency & Package Review

Perform a coverage-complete, evidence-backed review of the repository's software supply chain. Treat the result as a gate: never infer a clean result from partial discovery, an unavailable scanner, or unresolved critical evidence.

## Preserve the safety and authorization boundary

- Follow the user request and every applicable `AGENTS.md` before reviewing anything.
- Record `git status --short` before the review and again before handoff. Preserve existing user work.
- Keep an explicit review request read-only. Do not edit manifests, lockfiles, source, configuration, or reports unless separately authorized.
- For an already-authorized add, install, upgrade, replacement, or removal, complete the preflight gate first. Continue only when the gate permits it, use non-interactive resolver options that disable lifecycle scripts where available, then inventory and rescan the complete post-resolution graph.
- Treat authorization to change a dependency as authorization for that scoped change, not permission to execute arbitrary dependency build or lifecycle code. Ask separately before executing untrusted code, and require suitable isolation.
- Do not install scanners, package managers, runtimes, or helper packages during the review. Use only already-installed tools whose relevant mode is demonstrably non-mutating and non-executing.
- Do not run builds, imports, package lifecycle scripts, post-install hooks, Gradle or Maven plugins, Rust `build.rs`, setup code, container entrypoints, or reachability modes that compile or execute dependencies without explicit authorization and isolation. OSV-Scanner Rust call analysis executes dependency build scripts and is unsafe by default.
- Never expose credentials, tokens, private registry URLs, or private dependency coordinates. Automatically transmit only public package coordinates. Do not upload private manifests, lockfiles, SBOMs, source, or repository metadata without explicit authorization.
- Record every skipped action and the evidence it prevents. Critical gaps are `research-gated` and may force `BLOCKED`; they are never a clean result.

## 1. Establish scope and repository state

1. Confirm whether the request is a read-only review or already authorizes a dependency change.
2. Identify the repository root, comparison base when relevant, supported platforms, deployment targets, registry policy, license constraints, and risk tolerance from repository evidence.
3. For a proposed dependency change, record the intended package identity, ecosystem, purpose, requested constraint, source registry, and affected workspace before resolving or modifying anything.
4. Read the applicable sections of [references/ecosystem-evidence.md](references/ecosystem-evidence.md) before selecting commands.

## 2. Inventory every software input

Resolve this skill's installed directory, then run its bundled read-only inventory from that absolute script path. Do not assume the repository under review contains a `scripts/` directory:

```text
python <audit-dependencies-skill-directory>/scripts/inventory_dependency_files.py <repository-root> --format json
```

The versioned output uses repository-relative paths, redacts referenced coordinates by default, records unreadable, malformed, oversized, linked, or unavailable Git evidence under `gaps`, and lists every directory skipped by its generated/cache name policy under `exclusions`. Confirm each exclusion from repository context before treating it as generated; an ambiguous source-shaped `bin`, `build`, `env`, or similarly named tree remains a coverage obligation. Inspect sensitive coordinates directly in their local source file only when necessary; do not paste them into a command or report. Use the script as a discovery aid, not as the coverage conclusion. Inspect the returned files and supplement it with repository-specific evidence. Inventory all of the following:

- Direct and transitive language packages in every root, nested project, workspace, example, tool, test, and deployment project.
- Manifests, lockfiles, dependency constraints, workspace definitions, central version catalogs, build plugins, code generators, and package-manager configuration.
- CI actions, reusable workflows, CI plugins, downloaded tools, installer scripts, and release automation.
- Container base images, build-stage images, compose and orchestration images, package installations in image definitions, and development containers.
- Vendored or copied third-party code, generated clients with external runtimes, Git submodules, Git dependencies, binaries, archives, and checked-in tools.
- Runtime-loaded plugins, extensions, drivers, providers, models, browser assets, MCP servers, and other externally sourced executable or interpreted inputs.

Build a coverage ledger before scanning. Give every discovered input one of `covered`, `partially-covered`, `unsupported`, `private-not-transmitted`, `excluded-with-reason`, or `research-gated`. Do not exclude development, test, build, or operations dependencies merely because they are absent from the production runtime.

## 3. Resolve exact versions and integrity evidence

- Treat authoritative lockfiles, immutable image digests, Git commit SHAs, checksums, signed attestations, and installed-artifact metadata as exact resolution evidence.
- Permit manifest ranges when a current, consistent lockfile deterministically records the complete resolved graph. Do not require exact manifest pins when the ecosystem's lock model is authoritative.
- Resolve and distinguish direct, transitive, runtime, development, test, build, CI, container, vendored, and operational inputs. Count dependencies separately for every manifest or workspace scope.
- Check that each lockfile matches its manifest and workspace topology. A missing, stale, conflicting, or incomplete lockfile prevents an exact-graph claim.
- For a proposed change, establish the candidate's exact safe version and expected transitive closure before mutation when tooling and registry evidence allow it. If safe resolution would require executing package code, stop and request an isolated method instead.
- Verify registry identity, source URL, package namespace, integrity hashes, signatures, provenance, and digest or commit pinning where the ecosystem provides them.
- Label unresolved exactness explicitly. If uncertainty affects the proposed package or a potentially critical path, return `BLOCKED` rather than guessing.

## 4. Run safe vulnerability and integrity checks

- Prefer lockfile or SBOM analysis that does not install packages or execute project code. Use recursive OSV-compatible scanning and already-installed ecosystem-native audit tools when safe for the detected files.
- Before any networked scan, identify private coordinates and confirm exactly what the tool transmits. Use offline data or an explicitly filtered public-coordinate input when needed; never send an entire private lockfile or SBOM merely because the scanner accepts it.
- Before each command, confirm whether it can restore, resolve from private registries, run build plugins, execute lifecycle scripts, mutate lockfiles, generate caches, or upload repository data. Use safe flags or do not run it.
- Record the command, tool and version, input files, configuration, execution time, exit status, registry or database freshness, network use, and any ignored or unsupported inputs.
- Verify decision-critical findings against primary sources: maintainer advisories, official registries, OSV or GHSA records, authoritative release notes, and upstream security notices. Include URLs and access dates.
- Normalize aliases and withdrawn or disputed advisories. Deduplicate the same vulnerability across scanners without discarding ecosystem-specific evidence.
- Distinguish four separate states: package presence, affected installed version, reachable vulnerable code, and demonstrated exploitability. Do not present any one state as proof of the others.
- Treat scanner output as evidence, not authority. A clean scan only means no applicable result was found within that scanner's coverage and data freshness.
- If a scanner, advisory database, registry, or network service is unavailable, use only sufficiently fresh local or cached evidence and label the missing coverage. Return `BLOCKED` when the outage leaves critical candidate identity, exact-graph, integrity, or vulnerability evidence unresolved.

## 5. Assess broader supply-chain risk

Read [references/supply-chain-signals.md](references/supply-chain-signals.md) and assess proportionately:

- Package identity, registry origin, typosquatting, namespace takeover, and dependency-confusion risk.
- Provenance, signatures, attestations, reproducible-build evidence, integrity hashes, source-to-artifact linkage, and immutable pins.
- Ownership or maintainer changes, unusual release timing or cadence, compromised accounts, unpublished or replaced artifacts, and unexplained version or content anomalies.
- Lifecycle and build scripts, native code, prebuilt binaries, permissions, credential access, filesystem or process access, install-time or runtime network behavior, telemetry, and dynamic downloads.
- Maintenance status, security response, release support, compatibility, license obligations, abandonment indicators, and unnecessary dependency or transitive weight.
- CI action permissions and pinning, container image publishers and digests, submodule commits, vendored-source origin, and runtime extension trust boundaries.

Use OpenSSF Scorecard checks as project-risk signals and SLSA as a vocabulary for provenance and artifact integrity. Never turn either an aggregate score or a claimed SLSA level into an automatic pass or failure.

## 6. Apply the gate

Return exactly one top-level decision:

- `PASS`: coverage is sufficient, exact resolution is established for the relevant graph, and no material unresolved risk remains.
- `PASS_WITH_WARNINGS`: no blocking risk is established, but lower-risk findings, ordinary staleness, low-confidence maintenance signals, or non-critical coverage gaps require attention.
- `CONDITIONAL`: continuation is acceptable only with a named verified version, source, pin, configuration, isolation control, or other explicit condition. Re-evaluate after applying the condition.
- `BLOCKED`: a credible severe vulnerability, malicious or confused package identity, unacceptable privileged script or behavior, unsafe resolver path, unexpected graph drift, or unresolved critical evidence prevents safe continuation.

Block on credible severe risk; do not block solely because a package is old, unpopular, imperfectly scored, or named in a lower-risk advisory with evidence that the vulnerable path is unreachable. Explain confidence and the realistic failure or compromise path.

For an authorized dependency change:

1. Stop before mutation on `BLOCKED` or an unmet `CONDITIONAL` decision.
2. If the gate permits continuation, make only the authorized dependency change using safe resolver controls.
3. Compare the actual direct and transitive graph with the preflight expectation.
4. Re-run full inventory, exact-resolution checks, vulnerability checks, and supply-chain evaluation on the complete repository.
5. Reject unexpected or newly unsafe transitive changes. Do not silently accept resolver drift.

## 7. Report complete coverage and evidence

Lead with the gate decision and its consequence. Then report:

1. Scope, request mode, repository state, comparison base, and applicable policy.
2. A coverage ledger with `input/scope`, `ecosystem/class`, `manifest and lockfile`, `direct count`, `transitive count`, `exact-resolution and integrity source`, `scanner coverage`, `status`, and `gaps`.
3. Candidate or change details with exact proposed or selected versions, registry identity, expected and actual graph changes, and the gate result.
4. Findings ordered by severity and confidence. For each package finding include package identity, exact version, direct or transitive status, affected paths or scopes, advisory identifier, affected and fixed ranges, primary source, access date, reachability, exploitability limits, and remediation.
5. Supply-chain findings for CI, containers, vendored code, submodules, runtime extensions, scripts, provenance, integrity, licensing, maintenance, and dependency weight.
6. Commands and scanners run, tool versions, results, failures, database freshness, network use, skipped unsafe actions, and unexpected mutations.
7. Unsupported ecosystems, private inputs not transmitted, unresolved evidence, assumptions, and research gates.
8. Preflight-to-post-resolution graph differences when a change was authorized.
9. Final `git status --short` and whether repository state changed as authorized.

Include the complete exact-version inventory of packages that passed only when the user requests it; otherwise provide counts and list candidates, findings, changes, and exceptions. Never claim that the absence of findings proves the supply chain is secure.
