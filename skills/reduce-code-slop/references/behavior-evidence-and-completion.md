# Behavior, Evidence, and Completion

Use this reference to decide whether an apparent simplification is real, whether a proposed edit preserves behavior, and when the task is complete.

## Freeze the relevant contract

Describe the smallest useful behavior boundary before accepting a candidate. Derive it from repository evidence rather than an idealized redesign:

- callers and consumers, including dynamic or external consumers that can be inspected safely;
- tests, examples, documentation, schemas, protocol definitions, configuration, and supported environments;
- public names, signatures, serialized shapes, ordering, timing, side effects, state transitions, and persistence;
- exception types, status values, messages that form a supported interface, logging and metrics, retry behavior, and fallback semantics;
- cancellation, concurrency, resource ownership, disposal, dependency-injection lifetime, and process boundaries;
- framework discovery, reflection, annotations or attributes, generated code, and compatibility commitments.

Classify uncertain behavior as `unknown` and explain the verification gap. Do not silently choose a new contract because the current one looks awkward.

## Distinguish evidence from taste

Strong evidence includes executable checks, direct caller and data-flow inspection, compiler or type-checker results, reproducible runtime observations, authoritative project documentation, supported public contracts, and relevant history. A linter warning, code shape, file count, or common style preference is only a lead until its consequence is established.

A candidate needs all of the following:

1. **Observed surface:** the exact indirection, duplicated policy, type escape, hidden failure, ownership ambiguity, or change diffusion under review.
2. **Concrete cost or risk:** how it impairs correctness, diagnostics, safe change, testing, comprehension, or lifecycle ownership.
3. **Necessary behavior:** what callers and operators still require.
4. **Complete alternative:** a smaller semantic design that retains that behavior.
5. **Equivalence evidence:** checks capable of detecting a meaningful regression.
6. **Transfer analysis:** where complexity, validation, or ownership moves after the change.

Reject candidates that merely reduce lines, files, types, or explicit checks. Exempt a candidate when the apparent complexity is required by security, compatibility, generated boundaries, framework integration, performance evidence, recovery, protocol behavior, or a stable test seam.

## Candidate lifecycle

Track each candidate through these states:

- `candidate`: a concrete lead worth checking;
- `verifying`: the contract, consequence, and alternative are being tested;
- `accepted`: evidence supports the full finding and proposed scope;
- `narrowed`: a smaller finding or change survives verification;
- `rejected`: evidence does not support a useful finding;
- `exempted`: the surface is justified and should not be churned without new evidence.

`candidate` is the initial state, `verifying` is intermediate, and the remaining states are terminal.

Keep rejected candidates out of the final findings. Mention an exemption only when it materially explains why a tempting rewrite was not performed.

## Failure behavior

Simplification must not make failures quieter or more success-like. Preserve or improve, within the authorized contract:

- validation at trust and format boundaries;
- actionable exceptions or explicit error results;
- cancellation propagation and cleanup;
- logs, traces, and metrics needed to diagnose operational behavior;
- transactional and partial-failure behavior;
- retry and idempotency semantics.

Do not replace a broad catch with an equally opaque result, remove context that callers need, or normalize unexpected states into defaults. If changing failure semantics is desirable, treat it as a separate behavioral change rather than a simplification.

## Ownership and lifetime

Prefer one evident owner for mutable state, background work, disposable resources, caches, subscriptions, and synchronization. A simplification is incomplete if it removes a wrapper while leaving ambiguous ownership in several callers.

Check construction and teardown together. Preserve thread-safety, request or session isolation, cancellation ownership, deterministic cleanup, and framework-managed lifetimes. Avoid global state as a shortcut unless the established contract genuinely requires process-wide ownership.

## Verification and completion

Use the repository's existing checks at the narrowest stable seam that exercises the behavior. A trustworthy sequence is:

1. capture initial Git state and the relevant passing or known-failing baseline;
2. run focused tests, builds, type checks, linters, or a safe characterization path before editing when feasible;
3. make one coherent change;
4. replay the same checks and relevant neighboring checks;
5. compare contracts, diagnostics, generated or serialized output, ownership, and timing where affected;
6. inspect the final diff and restore task-created temporary state.

`SIMPLIFIED` requires an authorized edit, a credible equivalence argument, passing relevant checks, and no unexplained repository mutation. Use `BLOCKED` when unavailable dynamic consumers, proprietary runtime behavior, missing tooling, or an unsafe environment prevents a material contract from being checked. A completed focused review returns `REVIEWED`, including a verified no-finding result. For refactor or enforcement mode, use `NO_CHANGE` when the current design is justified or the available alternatives only relocate complexity.
