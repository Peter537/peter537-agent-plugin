# Code Review Domains

Use this reference as a routing matrix, not a requirement to manufacture a finding in every category. Follow repository conventions unless evidence supports changing them. Prefer a few consequential findings over a checklist dump.

## Contents

- Correctness and intent
- Readability and maintainability
- State models, data structures, and knowledge ownership
- Boundaries and interfaces
- Testability and tests
- Failure handling and resilience
- Performance and concurrency
- Files and project structure
- Change coherence and minimality
- Data, APIs, and integrations
- Configuration and operations
- Documentation, developer experience, and users
- Recommendation discipline

## Correctness and intent

- Identify the behavior the code promises through callers, tests, schemas, public contracts, and user-visible flows.
- Trace normal, boundary, empty, invalid, partial, retry, cancellation, and recovery paths where applicable.
- Look for incorrect state transitions, stale assumptions, ordering errors, unit or timezone mistakes, numeric overflow or precision loss, and inconsistent validation.
- Check whether comments, names, tests, and implementation disagree. Treat executable behavior as evidence, not automatically as intended product policy.
- Identify dead, unreachable, duplicated, obsolete, or speculative behavior only after verifying callers, reflection, registration, generation, and external entrypoints.

## Readability and maintainability

- Judge whether names expose domain meaning, invariants, ownership, units, and side effects.
- Look for hidden control flow, excessive nesting, distant mutation, boolean-flag APIs, duplicated policy, temporal coupling, global state, and surprising side effects.
- Prefer the repository's established idioms unless a local pattern creates measurable risk.
- Distinguish essential domain complexity from accidental structural complexity.
- Recommend abstraction only when it clarifies a stable concept, removes harmful repetition, or protects an evidenced public, platform, security, lifecycle, compatibility, generated-code, or nondeterministic boundary. Avoid premature generalization and unjustified single-use indirection.

## State models, data structures, and knowledge ownership

- Enumerate related booleans, nullable values, tags, statuses, lifecycle markers, and derived fields. Identify reachable invalid, stale, contradictory, or unrepresentable states before recommending a different model.
- Trace where invariants are established, validated, mutated, serialized, and reconstructed. Prefer one authoritative owner for rules about shape, units, identity, ordering, normalization, and lifecycle.
- Look for duplicated branching that implements one stable policy. Recommend a map, registry, reducer, command, typed state, or other structure only when it reduces caller knowledge, invalid states, or inconsistent policy rather than hiding branches.
- Inspect repeated scans, transformations, joins, and lookups. Recommend a different collection or index only when workload, update cost, memory, consistency, and lifecycle evidence make the change material.
- Trace retry, cancellation, concurrency, and asynchronous state for stale results, lost updates, duplicate completion, ambiguous ownership, and transitions that cannot be made atomic.
- Measure caller burden through required sequencing, preconditions, exposed representation, failure categories, and duplicated recovery logic.
- Prefer direct local code when a proposed abstraction adds more concepts, ownership boundaries, migration risk, or indirection than it removes.

## Boundaries and interfaces

- Check whether modules, functions, classes, services, and packages have coherent responsibilities and explicit inputs, outputs, side effects, and failure contracts.
- Examine dependency direction, cycles, leakage of infrastructure details, shared mutable state, and boundaries that make changes ripple unnecessarily.
- Review public APIs for compatibility, validation, error semantics, idempotency, pagination, cancellation, versioning, and misuse resistance as applicable.
- Prefer small interfaces shaped around consumer needs, while avoiding fragmentation that makes behavior harder to follow.
- Check that lifecycle, resource ownership, disposal, and transactional boundaries are unambiguous.

## Testability and tests

- Determine whether important behavior can be exercised deterministically without unnecessary network, clock, filesystem, process, or global-state coupling.
- Review the balance of unit, integration, contract, end-to-end, property, fuzz, and regression tests according to actual risk.
- Look for missing boundary and failure tests, brittle implementation-detail assertions, flaky timing, excessive mocks, unrealistic fixtures, and tests that can pass without proving behavior.
- Verify that security controls and authorization decisions have negative tests, not only successful paths.
- Do not recommend dependency injection, interfaces, or abstraction solely for testability when a simpler seam provides equivalent confidence.
- Evaluate whether a proposed refactor would reduce production clarity or performance more than it improves test isolation.

## Failure handling and resilience

- Trace error propagation, cleanup, rollback, retries, timeouts, cancellation, partial success, and restart behavior.
- Flag swallowed exceptions, ambiguous sentinel values, overly broad catches, retry storms, non-idempotent retries, lost context, and user-hostile failure messages.
- Verify resource cleanup for files, sockets, locks, transactions, processes, subscriptions, and temporary data.
- Check whether fallback behavior is safe, observable, bounded, and consistent with product expectations.
- Distinguish recoverable operational failures from programmer defects that should fail fast.

## Performance and concurrency

- Require a plausible workload, complexity argument, profiling evidence, or known hot path before treating micro-optimization as a finding.
- Inspect algorithmic growth, repeated I/O, unnecessary serialization, N+1 access, unbounded collections, cache invalidation, memory retention, startup cost, and excessive allocations where material.
- Review concurrency for races, deadlocks, starvation, ordering assumptions, duplicate work, unsafe shared state, lost cancellation, backpressure, and atomicity gaps.
- Check async code for blocking operations, detached tasks, unobserved failures, uncontrolled fan-out, and lifecycle leaks.
- State the expected performance or resource tradeoff of every structural recommendation.

## Files and project structure

- Treat line count as a discovery signal, never an automatic defect or split threshold.
- Consider splitting when a file owns unrelated responsibilities, changes for unrelated reasons, creates merge hotspots, hides important boundaries, or prevents focused testing and ownership.
- Keep a long file intact when its behavior is cohesive, sequential, navigable, and easier to understand together.
- Consider merging files when fragmentation creates indirection without independent ownership, reuse, lifecycle, or testing value.
- Before deleting or moving a file, verify imports, runtime registration, reflection, configuration, generated references, packaging, scripts, documentation links, and external consumers.
- Judge folder structure by reader tasks, dependency boundaries, and ownership rather than mechanically mirroring types or framework conventions.

## Change coherence and minimality

- Determine whether the reviewed change represents one coherent behavioral intent and whether every material edit contributes to it.
- Separate unrelated formatting, renames, moves, generated updates, debug residue, and refactoring when they obscure review, rollback, ownership, or causal verification.
- Prefer the smallest behaviorally complete root-cause change, not the smallest textual diff. Inspect sibling paths and shared policy before accepting a local guard.
- Require an evidenced present benefit for added abstractions, modes, extension points, configuration, persistent state, background work, public contracts, and operational obligations.
- Check whether local concision transfers complexity into callers, reflection, framework behavior, configuration, deployment, recovery, or tests.
- Do not infer authorship from unused constructs, duplicated helpers, invented APIs, hidden dependencies, or broad patch surface. Report only the observable defect and consequence.
- Preserve explicit duplication when similar code represents different policy or when a shared abstraction is demonstrably unstable. Do not impose a universal duplication threshold.
- Do not recommend patch reduction unless the alternative preserves relevant behavior, compatibility, security, operations, and verification.

## Data, APIs, and integrations

- Check schema constraints, migrations, transaction boundaries, concurrency control, nullability, uniqueness, indexing, retention, serialization, and backward compatibility.
- Review external calls for authentication, validation, timeouts, retries, idempotency, rate limits, pagination, partial responses, contract drift, and observability.
- Verify that caches, replicas, queues, and eventual consistency do not silently violate user-visible invariants.
- Identify destructive or irreversible operations and confirm authorization, confirmation, auditability, rollback, and recovery paths.
- Treat fixtures, example payloads, and generated clients as evidence only within their documented versions and environments.

## Configuration and operations

- Trace defaults, precedence, environment overrides, validation, secret sources, feature flags, and failure behavior for missing or invalid configuration.
- Inspect CI and release workflows for least privilege, pinned or trusted actions, artifact integrity, reproducibility, protected environments, and failure visibility.
- Review logs, metrics, traces, and alerts for actionable context without secrets, personal data, unbounded cardinality, or noisy duplication.
- Check health, readiness, graceful shutdown, backup, restore, migration, and rollback behavior when the repository operates a service or persistent system.
- Verify that development, test, staging, and production behavior differ intentionally rather than accidentally.

## Documentation, developer experience, and users

- Compare code, commands, configuration, APIs, and tests with README files, focused documentation, examples, and CLI help.
- Check whether a new contributor can discover supported workflows without relying on tribal knowledge.
- Review user-facing failures, keyboard and screen-reader behavior, localization, destructive-action safeguards, and performance feedback when relevant.
- Report documentation drift as a finding only when it creates a real implementation, operational, security, or user risk.

## Recommendation discipline

- Separate demonstrated defects from risk reductions, design improvements, and personal preferences.
- Explain why the current design fails under a concrete scenario before proposing a replacement.
- Prefer the smallest change that addresses root cause and preserves useful behavior.
- Check whether a recommendation worsens latency, throughput, memory, compatibility, operability, testability, or cognitive load elsewhere.
- Mark undefined product behavior or inaccessible evidence `research-gated`; do not invent policy.
- Avoid repeating the same root cause as many findings. Report the systemic issue and list representative affected locations.
