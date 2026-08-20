# Operational Retirement

Use this reference when a candidate represents a rollout, compatibility, data, or externally controlled lifecycle rather than ordinary unreachable code.

## Separate reachability from retirement

Operational surface can remain reachable after its purpose ends, and it can appear unreachable while still protecting an upgrade or rollback path. Establish both:

- **Technical liveness:** what code, configuration, data, or external state can select the path now.
- **Lifecycle obligation:** what supported users, versions, stored data, deployments, contracts, recovery procedures, or rollout commitments still require it.

Do not classify lifecycle code as `ready` until both questions are resolved.

## Feature flags and experiments

Map the flag key, owner, control plane, defaults, targeting rules, environment overrides, cached values, emergency use, and code branches. Repository configuration rarely proves the state of a remote flag service.

- Confirm that the rollout or experiment reached its intended terminal state across every supported environment and cohort.
- Determine which branch becomes permanent and whether tests, metrics, alerts, documentation, configuration, and cleanup jobs still encode the old split.
- Preserve kill switches and operational controls whose continuing purpose is evidenced, even when one branch is rarely observed.
- Treat flag deletion from an external service, analytics cleanup, or production rollout changes as separate authorized operations.
- If remote state is required but unavailable, use `research-gated`; if the owner must decide whether the control remains supported, use `needs-decision`.

## Shims, deprecations, and compatibility paths

Identify the compatibility promise, affected versions or clients, published deprecation notice, replacement, migration window, support policy, and known downstream consumers.

- An internal caller count cannot prove that a public API, file format, protocol version, CLI option, environment variable, route, or serialized name has no external users.
- Verify aliases and adapters from both directions. Removing only the wrapper can strand callers; removing only the old implementation can leave a misleading supported surface.
- Do not retire a security or validation compatibility path without confirming the replacement preserves the same trust and data-integrity boundaries.
- Use `needs-decision` when support policy or user communication must change, even if technical removal is straightforward.

## Migrations, backfills, and persisted state

Distinguish these cases:

- a schema migration retained as part of the authoritative migration chain;
- an upgrade path still needed by supported installations;
- a repeatable repair or import/export operation that remains a supported tool;
- a completed one-time backfill whose code may be retired after data-state and rollback evidence;
- an abandoned or disposable conversion requiring a privacy-focused review.

Before proposing removal, identify the oldest supported source state, deployed versions, database or file-format baselines, migration bookkeeping, backups, disaster recovery, rollback behavior, replicated or offline clients, and release packaging. A successful run in one environment does not prove completion everywhere.

Never execute a migration, mutate stored data, drop schema objects, or delete backups under this skill. Route a dedicated disposable-migration or embedded-data exposure review to `$audit-data-exposure` when available.

## Routes, jobs, assets, and operational hooks

- Check reverse proxies, schedulers, queues, webhooks, service discovery, infrastructure manifests, monitoring, runbooks, support tooling, and external integrations.
- Treat health, readiness, metrics, recovery, maintenance, and administrative paths as operational entrypoints even when ordinary product flows do not call them.
- Verify assets through build pipelines, templates, runtime URLs, manifests, content-security rules, localization, and downstream packaging; source imports alone are insufficient.
- Treat startup and shutdown registration as behavior. Removing an apparently unused initializer can remove side effects, resource cleanup, security registration, or diagnostics.

## Form a complete retirement batch

A coherent operational batch may include the retired path, registrations, configuration, tests for the obsolete branch, documentation, metrics, alerts, dashboards, cleanup logic, and ownership metadata. Include only surfaces whose sole contract is the approved retirement.

Keep dependency removal, remote control-plane changes, data mutation, deployments, and compatibility-policy changes as separately authorized actions even when they are prerequisites. Report the order and stop at the current authority boundary.

## Primary references

Accessed 2026-08-20.

- [OpenFeature flag-evaluation specification](https://openfeature.dev/specification/sections/flag-evaluation/) describes provider-controlled evaluation context, defaults, reasons, errors, and variant metadata that can make repository-only reasoning incomplete.
- [Microsoft feature-management reference](https://learn.microsoft.com/en-us/azure/azure-app-configuration/feature-management-dotnet-reference) documents configuration-driven filters, variants, targeting, and runtime feature evaluation.
- [EF Core migration management](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/managing) explains migration history, removal limits, and the relationship between migrations and database state.
- [Kubernetes API deprecation policy](https://kubernetes.io/docs/reference/using-api/deprecation-policy/) is an example of versioned compatibility obligations that outlive internal call references.
