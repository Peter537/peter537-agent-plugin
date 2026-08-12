# Security and Supply-Chain Review

Use this reference for whole-repository, security, dependency, configuration, CI, deployment, and public-interface audits. Adapt it to the repository's threat model and technology; do not apply web-only controls to unrelated software.

## Contents

- Establish the threat model
- Review security boundaries
- Protect secrets and sensitive data
- Inventory dependencies
- Decide whether a dependency is justified
- Research vulnerabilities and versions
- Interpret tools and evidence
- Method sources

## Establish the threat model

- Identify assets, sensitive data, trust levels, actors, entrypoints, privileged operations, and external systems.
- Trace attacker-controlled input across parsing, validation, authorization, storage, rendering, logging, and outbound requests.
- Determine deployment exposure, tenant boundaries, privilege levels, authentication assumptions, and consequences of compromise.
- Use realistic abuse and failure paths. Do not assign severity from a keyword or vulnerability class alone.
- Record assumptions about infrastructure or controls outside the repository and mark unverified controls `research-gated`.

## Review security boundaries

- Verify authentication, session lifecycle, credential recovery, authorization at every privileged operation, and deny-by-default behavior.
- Check object-level and function-level authorization, tenant isolation, role changes, impersonation, administrative paths, and confused-deputy risks.
- Review input validation and output encoding for query, command, template, header, log, path, expression, and markup injection.
- Inspect filesystem paths, archives, uploads, downloads, redirects, outbound requests, URL parsing, and network destinations for traversal, overwrite, server-side request forgery, and unsafe schemes.
- Review deserialization, reflection, dynamic loading, plugins, regular expressions, parsers, and native or process execution for unsafe inputs and resource limits.
- For applicable web software, inspect cross-site scripting, request forgery, cross-origin policy, clickjacking, cookies, caching, browser storage, and content security controls.
- Check cryptographic purpose, algorithms, modes, key generation, storage, rotation, randomness, comparison, and failure behavior against current platform and standards guidance.
- Examine abuse controls, rate limits, quotas, request sizes, decompression, recursion, algorithmic complexity, queue growth, and other denial-of-service paths.
- Review errors, logs, diagnostics, source maps, debug endpoints, and telemetry for information disclosure or unsafe operational access.
- Inspect infrastructure and CI for excessive permissions, untrusted code execution, unsafe pull-request contexts, mutable third-party actions, artifact tampering, and insecure deployment defaults.

## Protect secrets and sensitive data

Keep this section proportionate within a broad code or security audit. Route a dedicated personal-data, anonymization, repository data-exposure, or disposable-migration review to `$audit-data-exposure` when available.

- Search tracked content, history when relevant, configuration, fixtures, examples, logs, CI, and generated artifacts using configured secret-scanning tools where available.
- Never print or quote a discovered credential. Report its type and location with the value redacted.
- Treat a committed secret as potentially compromised even if later removed; recommend revocation or rotation according to its authority and exposure.
- Trace collection, use, retention, export, deletion, encryption, access, logging, and third-party transfer of personal or sensitive data.
- Distinguish public identifiers from credentials and sensitive metadata. Avoid creating a secret-shaped false positive without validation.

## Inventory dependencies

- Identify manifests, lockfiles, vendored code, submodules, build plugins, CI actions, containers, base images, generated clients, and runtime-loaded extensions.
- Classify dependencies as direct or transitive and runtime, development, build, test, or operational.
- Resolve the installed or locked version rather than relying only on a declared range.
- Search actual imports, registrations, generated use, CLI invocation, configuration, and packaging before calling a dependency unused.
- Note duplicate libraries, overlapping capabilities, multiple versions, unbounded version ranges, unpinned remote actions, and absent lock or integrity data when relevant.
- Evaluate maintenance, ownership, provenance, release practices, compromise history, permissions, install scripts, native code, network behavior, license obligations, and ecosystem health.

## Decide whether a dependency is justified

- Compare the dependency's real behavior with standard-library, platform, framework, or already-installed capabilities.
- Include transitive weight, bundle or startup cost, build complexity, update burden, attack surface, specification edge cases, and maintenance ownership.
- Recommend removal when usage is absent, redundant, or safely replaceable by a small and stable non-security-sensitive implementation with lower lifetime cost.
- Do not equate few call sites with trivial behavior. Parsers, encoders, time handling, Unicode, protocols, file formats, and compatibility helpers often hide extensive edge cases.
- Prefer maintained, well-vetted libraries for cryptography, authentication, authorization, security protocols, serialization, and complex standards.
- Treat adding a dependency similarly: require meaningful value, compatible licensing, acceptable provenance, and a maintained release path.

## Research vulnerabilities and versions

- Use current authoritative evidence. Prefer maintainer advisories, official registries, OSV records, national vulnerability databases, release notes, and standards bodies over unsourced summaries.
- Record package ecosystem and name, locked version, advisory ID, affected range, fixed range, publication or update date, source URL, and access date.
- Verify whether the vulnerable component, feature, configuration, and execution path are present. Keep `dependency present`, `vulnerable version`, `reachable path`, and `demonstrated exploitability` as separate claims.
- Do not treat `outdated` as a vulnerability. Explain the security, compatibility, support, correctness, or maintenance benefit of an upgrade.
- Review intermediate release notes and migration guidance before recommending a target version. Account for runtime requirements, breaking changes, removed APIs, data migrations, and lockfile effects.
- Compare conflicting advisories by package identity, version scheme, affected component, date, authority, withdrawn status, and deployment applicability.
- If current metadata cannot be retrieved, report the last verified state and make the conclusion `research-gated` rather than guessing.

## Interpret tools and evidence

- Prefer repository-configured scanners and ecosystem-native audit commands. Do not install a scanner or mutate dependency state without explicit authorization.
- Public registry or advisory lookups may transmit only public package coordinates. Do not use private-registry credentials or upload manifests, source, SBOMs, or repository data without authorization.
- Preserve the exact command, tool version when discoverable, timestamp, exit status, relevant configuration, and result summary.
- Validate decision-critical results against the underlying advisory or primary source. Deduplicate aliases such as CVE, GHSA, and OSV identifiers.
- Treat a scanner's clean result as limited to its database, configuration, supported ecosystems, and executed paths.
- Treat static reachability as evidence, not proof that dynamic loading, reflection, alternate entrypoints, or deployed configuration cannot expose a path.
- Report inaccessible sources, unsupported ecosystems, stale advisory databases, authentication failures, and tool crashes as verification gaps.

## Method sources

Use these as methodological anchors and verify their current versions and applicability at audit time:

- [OWASP Code Review Guide](https://owasp.org/www-project-code-review-guide/) for manual secure-code-review practice.
- [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/) for applicable application-security controls.
- [NIST Secure Software Development Framework](https://csrc.nist.gov/pubs/sp/800/218/final) for secure-development practices and remediation of root causes.
- [OSV-Scanner documentation](https://google.github.io/osv-scanner/) for open-source vulnerability and dependency scanning concepts.
- [OpenSSF Scorecard](https://scorecard.dev/) for assessing open-source and supply-chain project risk through automated checks.
