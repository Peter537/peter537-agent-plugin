# Supply-Chain Signals and Evidence

Use these signals to investigate and explain risk. No single signal, badge, score, advisory, signature, or popularity metric proves that a package is safe or unsafe.

## Contents

- [Normalize evidence](#normalize-evidence)
- [Identity and dependency confusion](#identity-and-dependency-confusion)
- [Vulnerabilities and exploitability](#vulnerabilities-and-exploitability)
- [Provenance and integrity](#provenance-and-integrity)
- [Maintainers and releases](#maintainers-and-releases)
- [Executable behavior and privilege](#executable-behavior-and-privilege)
- [Maintenance, licensing, and weight](#maintenance-licensing-and-weight)
- [Decision guidance](#decision-guidance)
- [Primary references](#primary-references)

## Normalize evidence

- Identify a component with ecosystem, normalized package name, exact version or commit, source registry or repository, package URL when available, integrity value, and affected repository scopes.
- Label claims `observed`, `inferred`, `assumed`, or `unknown/research-gated` when the distinction affects a decision.
- Prefer maintainer advisories, official registries and repositories, OSV/GHSA records, standards bodies, signed transparency records, and authoritative release notes. Record the URL and access date.
- Reconcile conflicting sources by identity, affected artifact, version range, publication and modification date, withdrawal status, configuration, platform, and vulnerable symbol or behavior.
- Automatically research only public package coordinates. Keep private names, registries, manifests, lockfiles, SBOMs, source paths, credentials, and internal metadata local unless the user explicitly authorizes transmission.

## Identity and dependency confusion

- Confirm spelling, namespace or scope, publisher, registry, repository link, signing identity, and expected ownership. Compare lookalike names, punctuation changes, homoglyphs, new scopes, and suspiciously similar descriptions.
- Inspect registry precedence, scoped-registry rules, internal package names, namespace reservation, fallback behavior, and public/private version ordering. A valid public package can still create dependency-confusion risk.
- Verify aliases, forks, renamed packages, deprecated names, transfers, and replacement recommendations from primary sources. Do not infer continuity from a similar name.
- Treat an identity mismatch, unexplained publisher change, unexpected registry, or higher public version shadowing a private name as critical until resolved.

## Vulnerabilities and exploitability

- Separate package presence, an affected exact version, reachable vulnerable code, and demonstrated exploitability. State which level the evidence supports.
- Verify affected and fixed ranges against the package ecosystem's version semantics. Check backports, distribution patches, withdrawn advisories, platform conditions, optional features, and configuration prerequisites.
- Do not suppress a severe advisory solely because reachability is unknown. Do not call a package exploitable solely because a scanner found its name and version.
- For transitive findings, identify every introducing path and the nearest direct dependency or build input that can remediate it.
- Check malicious-package and compromise advisories as well as conventional CVEs. Removal, credential rotation, cache invalidation, or incident response may be required even when no fixed version exists.

## Provenance and integrity

- Determine whether the downloaded artifact can be tied to the intended source revision and authorized build process. Look for signed provenance, transparency-log entries, attestations, reproducible builds, and source-to-artifact correspondence.
- Use SLSA terminology to describe build provenance and integrity controls. Verify the actual predicate, subject digest, builder identity, source, parameters, and trust root; a claimed level or badge is not sufficient.
- Verify lockfile hashes, registry integrity fields, checksums, signatures, Git commit SHAs, OCI digests, and CI action SHAs. Confirm that the integrity value covers the consumed artifact rather than only metadata.
- Treat missing provenance as a risk signal whose severity depends on artifact privilege and exposure. Treat invalid or mismatched integrity evidence as a likely blocker.

## Maintainers and releases

- Investigate recent ownership transfers, new maintainers, dormant accounts becoming active, deleted history, forced tag changes, registry-publisher changes, compromised credentials, and unexplained repository moves.
- Compare release cadence, version jumps, artifact size and contents, dependency graph changes, install scripts, binary additions, release timing, and source tags. A single anomaly is a lead, not proof.
- Check whether the exact artifact predates or follows a reported compromise and whether mirrors, caches, or lockfiles can still supply the affected content.
- Use OpenSSF Scorecard checks such as maintained status, pinned dependencies, dangerous workflows, token permissions, code review, signed releases, and packaging as investigation prompts. Do not use the aggregate score as a gate by itself.

## Executable behavior and privilege

- Inspect install, prepare, post-install, build, plugin, generator, and uninstall scripts without executing them. Follow referenced scripts and downloaded URLs statically where possible.
- Identify native extensions, prebuilt binaries, WebAssembly, shell or PowerShell, compiler plugins, macros, annotation processors, dynamic imports, reflection-based loading, and code generation.
- Map filesystem, process, network, environment, credential, browser, cloud, CI token, and package-registry access at install, build, test, and runtime.
- Flag dynamic downloads, unpinned executables, telemetry, self-update behavior, obfuscation, encoded payloads, undeclared network access, and architecture-specific artifacts for deeper verification.
- Judge behavior against package purpose. A compiler or browser automation package needs capabilities that would be anomalous in a formatting or data-only package.

## Maintenance, licensing, and weight

- Check supported versions, security policy and response history, release recency, unresolved critical issues, maintainer capacity, deprecation status, and compatibility with the repository's runtimes.
- Verify declared and artifact-level licenses, notices, source-offer obligations, copyleft compatibility, patent terms, export constraints, and differences across bundled or transitive components. Escalate legal uncertainty rather than giving legal conclusions.
- Measure new direct and transitive count, duplicate versions, download and installed size, native toolchain requirements, runtime surface, update burden, and alternative platform capabilities.
- Verify actual usage before recommending removal. Never replace mature cryptography, authentication, authorization, parsing, serialization, or protocol implementations merely to reduce package count.
- Treat low popularity, a small maintainer team, or ordinary staleness as contextual warnings unless combined with stronger evidence of abandonment, compromise, or unacceptable operational risk.

## Decision guidance

- Block credible malicious identity, dependency confusion, severe applicable vulnerabilities without an acceptable control, invalid integrity, unacceptable privileged behavior, or unresolved critical evidence about a proposed exact graph.
- Use `CONDITIONAL` only when a concrete verified version, source, digest, configuration, isolation control, or graph constraint would make continuation acceptable.
- Use warnings for lower-risk unreachable advisories, modest staleness, low-confidence maintenance signals, non-critical provenance gaps, or manageable license and weight concerns.
- Record the control owner and verification step for every condition. Re-run the complete graph after an authorized resolution because a safe candidate can still introduce unsafe transitive changes.

## Primary references

- [OSV schema](https://ossf.github.io/osv-schema/)
- [GitHub Advisory Database](https://github.com/advisories)
- [OpenSSF Scorecard](https://scorecard.dev/)
- [SLSA specification 1.2](https://slsa.dev/spec/v1.2/)
- [in-toto Attestation Framework](https://github.com/in-toto/attestation)
- [SPDX specifications](https://spdx.dev/specifications/)
- [CycloneDX specifications](https://cyclonedx.org/specification/overview/)
