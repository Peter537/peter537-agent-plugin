# Evidence Layers and Playbooks

Choose only the layers required by each acceptance claim. More checks do not compensate for a missing decisive layer.

## Evidence layers

### Static and build evidence

Use source inspection, type checking, compilation, schemas, manifest parsing, and package or archive inspection for structural claims. These checks can prove that a contract is present or an artifact is well formed; they do not prove runtime behavior unless the claim is purely static.

### Component and repository tests

Use existing tests when their fixture, seam, and assertions exercise the acceptance claim. Confirm the test can distinguish an invalid state or behavior. A passing test that asserts implementation details or omits the reported workflow is supporting context, not complete proof.

### API evidence

Capture request identity, authenticated role, response status and semantics, relevant headers or protocol state, and controlled input. Verify error behavior when rejection is part of the contract. A successful response alone does not prove durable storage, downstream effects, or UI behavior.

### UI evidence

Exercise user-visible behavior through an existing safe browser or application path. Verify the relevant action, state transition, error handling, accessibility interaction, and durable result where required. A screenshot proves only captured pixels; DOM presence does not prove interactivity.

Playwright's official [best practices](https://playwright.dev/docs/best-practices) emphasize user-visible behavior, isolated tests, controlled data, and resilient assertions. Apply those principles when an existing Playwright path is available; do not add Playwright merely for this workflow.

### Persistence evidence

Observe state before the action, after it, and after the required boundary such as restart, reload, reconnect, or a second client. Verify populated and upgraded state when the claim concerns migration or compatibility; an empty database is not representative proof.

### Operational evidence

Use existing logs, traces, metrics, health endpoints, and correlation identifiers to connect a request or operation across boundaries. Keep each signal's limits explicit. The OpenTelemetry [observability primer](https://opentelemetry.io/docs/concepts/observability-primer/) describes traces, metrics, and logs as distinct telemetry signals; no single signal automatically proves the full user outcome.

### Native and platform evidence

Use the actual native host, device capability, packaging path, lifecycle, and platform-specific accessibility checks when the claim names them. Browser or companion-host evidence may verify shared presentation behavior but cannot prove native WebView, device API, lifecycle, installer, or package behavior.

## Focused and realistic passes

Start with a focused proof that isolates the criterion cheaply. Then replay the realistic path when required interactions, integrations, restarts, permissions, or state transitions were excluded by the focused seam. Keep inputs comparable across attempts and record deliberate differences.

Check relevant failure behavior. Expected rejection is a successful verification when the contract requires rejection and the observable status, message semantics, and state preservation match that contract.

## Intermittent and ordering behavior

Use repository-established repetition, ordering, or concurrency conditions. When none exist, define a bounded trial plan from the claim and available time rather than inventing a universal threshold. Report runs, failures, ordering, and environment. One success never proves absence of a flake.

## Performance behavior

Use the repository's stated budget, baseline, workload, warmup, environment, and measurement method. Compare like with like and retain distributions or repeated measurements when available. Do not declare improvement from one timing or compare different builds, data sizes, or machines without bounding the conclusion.

## Migration and compatibility behavior

Exercise representative prior state, populated data, supported versions, rerun or restart behavior, and rollback or failure behavior when those are part of the contract. Inspect preserved identifiers, ordering, relationships, and irreversible effects without revealing record contents. Do not execute a production migration.

## CI-only evidence

Use exact-revision CI evidence when local reproduction is unavailable. Record missing artifacts, logs, environment parity, and retry information. Return `BLOCKED` if the acceptance claim requires a behavior that the retained CI evidence does not directly establish.
