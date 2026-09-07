# Security Review

Use this reference when an audit includes trust boundaries, authentication, authorization, untrusted input, secrets, sensitive operations, public interfaces, or AI-enabled behavior. Adapt controls to the repository's threat model; do not apply web or AI controls to unrelated software.

## Contents

- Establish the threat model
- Review identity, privilege, and trust boundaries
- Review untrusted input and sensitive operations
- Review cryptography, resilience, and diagnostics
- Protect secrets and sensitive data
- Review AI-enabled systems when applicable
- Interpret evidence and current standards

## Establish the threat model

- Identify protected assets, sensitive data, actors, entrypoints, privilege levels, tenant boundaries, external systems, and consequences of compromise.
- Trace attacker-controlled input through parsing, validation, authorization, transformation, persistence, rendering, logging, and outbound calls.
- Establish deployment exposure, identity assumptions, administrative capabilities, and relevant controls outside the repository. Mark inaccessible or unverified controls `research-gated`.
- Use realistic abuse and failure paths. Do not derive severity from a vulnerability name, keyword, or checklist category alone.

## Review identity, privilege, and trust boundaries

- Verify authentication, session lifecycle, credential recovery, identity changes, and termination behavior where applicable.
- Check authorization at every privileged operation, not only at navigation or presentation boundaries. Review object-level and function-level access, tenant isolation, role changes, impersonation, administrative paths, and confused-deputy risks.
- Prefer deny-by-default behavior with explicit ownership of policy, resource identity, and enforcement. Look for authorization logic duplicated inconsistently across callers.
- Review service, process, filesystem, network, database, cloud, and CI identities for least privilege, bounded credentials, and safe failure behavior.
- Confirm that security controls have negative and cross-boundary tests, not only successful-path coverage.

## Review untrusted input and sensitive operations

- Inspect validation and output encoding for query, command, template, header, log, path, expression, and markup injection.
- Review filesystem paths, archives, uploads, downloads, redirects, outbound requests, URL parsing, and network destinations for traversal, overwrite, unsafe schemes, and server-side request forgery.
- For uploads, trace byte limits through request parsing, validation, and storage. Record a handler's absent size check separately from unverified upstream limits, and assess memory or storage exhaustion within that evidence boundary. Include size enforcement in remediation and negative tests; fixing filename traversal or active-content serving does not establish bounded resource use. Preserve equivalent limits when their enforcement is evidenced.
- Examine deserialization, reflection, dynamic loading, plugins, regular expressions, parsers, native calls, and process execution for unsafe inputs, surprising authority, and resource limits.
- For applicable web software, review cross-site scripting, request forgery, cross-origin policy, clickjacking, cookies, browser storage, caching, and content security controls.
- Identify destructive or irreversible operations and verify authorization, confirmation, auditability, rollback, recovery, idempotency, and partial-failure behavior.

## Review cryptography, resilience, and diagnostics

- Establish the cryptographic purpose before evaluating algorithms, modes, key generation, storage, rotation, randomness, comparisons, certificates, and failure behavior against current platform or standards guidance.
- Do not recommend handwritten cryptography, authentication, authorization, or security protocols merely to reduce dependencies or implementation size.
- Examine rate limits, quotas, request sizes, decompression, recursion, algorithmic complexity, queue growth, and other denial-of-service paths.
- Review retries, timeouts, cancellation, circuit breaking, backpressure, cleanup, and recovery for behavior that remains bounded under attacker or failure pressure.
- Inspect errors, logs, traces, diagnostics, source maps, debug endpoints, and telemetry for information disclosure, excessive privilege, unsafe access, or missing incident context.

## Protect secrets and sensitive data

Keep this coverage proportionate within a broad code or security audit. Route a dedicated personal-data, anonymization, repository data-exposure, or disposable-migration review to `$audit-data-exposure` when available.

- Search tracked content, relevant history, configuration, fixtures, examples, logs, CI, and generated artifacts using already-configured secret scanners when safe.
- Never print or quote a discovered credential or private value. Report its category and location with the value redacted.
- Treat a committed secret as potentially compromised even after removal; recommend containment and rotation appropriate to its authority and exposure.
- Trace collection, use, retention, export, deletion, encryption, access, logging, and third-party transfer of personal or sensitive data when material to the broader audit.
- Distinguish intentionally public attribution and identifiers from credentials and private metadata. Validate secret-shaped candidates before reporting them.

## Review AI-enabled systems when applicable

Apply AI-specific controls only when the product itself uses models, training or retrieval data, embeddings, agents, MCP, model supply chains, or AI-specific lifecycle behavior. The possible use of an AI coding assistant does not make an ordinary application an AI-enabled system.

- Establish model and data provenance, intended capability, autonomy, tool authority, trust boundaries, and human control.
- Review prompt and content injection, unsafe tool invocation, cross-tenant or context leakage, retrieval poisoning, excessive agency, output handling, and model-specific denial of service where applicable.
- Review evaluation, monitoring, fallback, rollback, model or prompt updates, and the consequences of nondeterministic behavior.
- Treat OWASP AISVS as a control source for applicable AI systems, not as proof of security or a universal checklist.

## Interpret evidence and current standards

- Map findings only to controls that fit the product, threat model, and requested assurance scope. A missing control is material only when the corresponding risk applies.
- When mapping to OWASP ASVS, record the stable version and use a version-qualified requirement identifier such as `v5.0.0-1.2.5`. Recheck the stable release at audit time.
- Treat the OWASP Code Review Guide as a source of manual review technique. Its published guide is historical and must not be the sole current vulnerability-control baseline.
- Preserve the command, tool version when discoverable, timestamp, configuration, exit status, and concise result summary for automated checks.
- Treat scanner results as candidates. Validate decision-critical results against repository behavior and primary sources, and report unsupported technologies or inaccessible controls as gaps.

## Method sources

Version-sensitive statuses below were verified on 2026-08-19 and must be rechecked when used:

- [OWASP Application Security Verification Standard](https://owasp.org/www-project-application-security-verification-standard/): ASVS 5.0.0 was the stable release and defines version-qualified requirement IDs.
- [OWASP Artificial Intelligence Security Verification Standard](https://owasp.org/www-project-artificial-intelligence-security-verification-standard-aisvs-docs/): AISVS 1.0 was current for applicable AI-enabled systems.
- [OWASP Code Review Guide](https://owasp.org/www-project-code-review-guide/): manual secure-review technique and historical vulnerability guidance.

Use these as methodological anchors, not legal certification, penetration-test evidence, or proof that every relevant control is implemented.

Upload guidance checked on 2026-09-07:

- [OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html#upload-and-download-limits): upload size limits protect storage capacity; inspect expanded sizes when decompression applies.
