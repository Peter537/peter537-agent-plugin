# Supply-Chain Review

Use this reference when an audit includes dependencies, manifests, lockfiles, build plugins, CI actions, containers, released artifacts, provenance, SBOMs, or vulnerability evidence. Keep broad-audit coverage proportionate and route a dependency-only review or package-change gate to `$audit-dependencies` when available.

## Contents

- Inventory software inputs
- Decide whether a dependency is justified
- Research vulnerabilities and versions
- Review release provenance and artifact integrity
- Review SBOM and VEX evidence
- Interpret tools and incomplete evidence
- Method sources

## Inventory software inputs

- Identify manifests, authoritative lockfiles, workspaces, vendored code, submodules, build plugins, CI actions, containers, base images, generated clients, toolchains, and runtime-loaded extensions.
- Classify dependencies as direct or transitive and runtime, development, build, test, or operational.
- Resolve installed or locked versions and immutable identifiers rather than relying only on declared ranges or mutable tags.
- Search imports, registrations, generated use, CLI invocation, configuration, packaging, deployment, and dynamic loading before calling a dependency unused.
- Note overlapping libraries, multiple versions, unbounded ranges, mutable remote actions, missing locks, absent integrity data, privileged install scripts, native code, and network behavior when relevant.
- Record unsupported ecosystems, missing lockfiles, unavailable submodules, unresolved images, or incomplete generated inputs as coverage gaps.

## Decide whether a dependency is justified

- Compare the dependency's real behavior with repository, language, standard-library, platform, framework, and already-installed capabilities.
- Evaluate correctness, specification edge cases, security and update history, ownership, transitive weight, bundle or startup cost, build complexity, permissions, licensing, API stability, and migration or removal cost.
- Recommend removal only when use is absent, redundant, or safely replaceable by a small stable non-security-sensitive implementation with lower lifetime cost.
- Do not equate few call sites with trivial behavior. Parsing, encoding, Unicode, time, archives, protocols, file formats, compatibility, and security often hide extensive edge cases.
- Prefer maintained, well-vetted libraries for cryptography, authentication, authorization, security protocols, serialization, and complex standards.
- Treat a proposed addition with the same discipline: require material value, compatible licensing, acceptable provenance, predictable installation behavior, and a maintained release path.

## Research vulnerabilities and versions

- Prefer maintainer advisories, official registries, OSV records, national vulnerability databases, release notes, and other primary sources over summaries.
- Record ecosystem, package, resolved version, advisory ID, affected and fixed ranges, publication or update date, source URL, and access date.
- Keep `dependency present`, `affected version`, `reachable path`, and `demonstrated exploitability` as separate claims.
- Use CISA's Known Exploited Vulnerabilities catalog as evidence of exploitation in the wild and an input to implementation order, not proof that the repository exposes the affected path.
- Do not treat ordinary staleness as a vulnerability. Explain the security, compatibility, support, correctness, or maintenance value of an upgrade.
- Review intermediate release notes and migration guidance before recommending a target. Account for runtime requirements, breaking changes, removed APIs, data migrations, and lockfile effects.
- Compare conflicting advisories by package identity, version scheme, affected component, date, authority, withdrawn status, and deployment applicability.
- If current metadata is unavailable, report the last verified state and mark the conclusion `research-gated` rather than guessing.

## Review release provenance and artifact integrity

- Identify released or deployed artifacts, their source revisions, builders, inputs, subjects, signing identities, distribution paths, and consumer verification policies.
- Where provenance or attestations exist, verify builder identity, source repository and revision, build inputs, materials, parameters, and artifact subjects against the expected release process.
- Review whether consumers or deployment systems verify signatures, attestations, digests, and trusted builder identities, including failure behavior when evidence is absent or invalid.
- Inspect release workflows for least privilege, isolated trusted builders, reproducibility, protected environments, immutable dependencies, and resistance to artifact substitution.
- Treat missing provenance as material only when the product's threat model, distribution model, procurement requirements, or release policy makes substitution a realistic concern.
- Treat SLSA levels and attestations as structured evidence. They do not replace source review, dependency analysis, or repository-specific verification.

## Review SBOM and VEX evidence

- Determine whether an SBOM is required or useful for distributed software, regulated procurement, incident response, customer disclosure, or complex dependency inventories.
- Check component identity, version, supplier, relationships, generation point, completeness, freshness, and linkage to the exact artifact.
- Treat an SBOM as an inventory aid, not proof that listed components are safe or that unlisted components are absent.
- Use VEX statements to record affected, not-affected, fixed, or under-investigation status only when the product, artifact, advisory, and justification match.
- Verify not-affected rationales against actual reachability, configuration, build composition, and deployment. Do not accept a VEX assertion solely because it exists.

## Interpret tools and incomplete evidence

- Prefer repository-configured scanners and ecosystem-native audit commands. Do not install a scanner, resolve new packages, or mutate dependency state without explicit authorization.
- Public registry or advisory lookups may transmit only public package coordinates. Do not use private-registry credentials or upload manifests, source, SBOMs, or repository data without authorization.
- Preserve the exact command, tool version when discoverable, timestamp, exit status, relevant configuration, database freshness, and result summary.
- Validate decision-critical scanner results against the underlying advisory, registry, release, or repository evidence. Deduplicate aliases such as CVE, GHSA, and OSV identifiers.
- Treat a clean scan as limited to its database, configuration, supported ecosystems, resolved inputs, and executed paths.
- Treat static reachability as evidence, not proof that reflection, alternate entrypoints, dynamic loading, or deployed configuration cannot expose a path.
- Treat OpenSSF Scorecard checks and aggregate scores as investigation signals, not standalone approval or rejection criteria.
- Report authentication failures, unsupported ecosystems, stale databases, missing artifacts, unavailable sources, and tool crashes as verification gaps.

## Method sources

Version-sensitive statuses below were verified on 2026-08-19 and must be rechecked when used:

- [NIST Secure Software Development Framework 1.1](https://csrc.nist.gov/pubs/sp/800/218/final): the final SSDF publication at verification time.
- [NIST SSDF 1.2 Initial Public Draft](https://csrc.nist.gov/pubs/sp/800/218/r1/ipd): draft material that must remain labeled as draft until superseded by a final publication.
- [SLSA specification v1.2](https://slsa.dev/spec/v1.2/): approved guidance for provenance and artifact verification.
- [OSV-Scanner documentation](https://google.github.io/osv-scanner/): dependency and vulnerability scanning concepts.
- [OpenSSF Scorecard](https://scorecard.dev/): automated project-risk checks used as leads rather than verdicts.
- [CISA Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog): exploitation-in-the-wild evidence.
- [CISA SBOM resources](https://www.cisa.gov/topics/cyber-threats-and-advisories/sbom): SBOM and VEX concepts and resources.

Use these sources as methodological anchors. Verify current versions, product applicability, and primary evidence at audit time.
