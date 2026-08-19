# C# Simplification Guidance

Use this reference only for C# work. Treat compiler and analyzer output as evidence about a configured build, not as a complete statement of runtime behavior.

## Nullability and type evidence

- Prefer type flow that proves a value is present over repeated null-forgiving operators, unchecked casts, or conversions through `object` or `dynamic`.
- The null-forgiving operator changes nullable-warning analysis only; it performs no runtime check. Accept it when external evidence really establishes the invariant and that evidence cannot be expressed more clearly at the boundary.
- Validate untrusted, deserialized, reflected, interop, configuration, and framework-bound values at the boundary. Do not scatter defensive checks through internal code once a trusted invariant is established.
- Preserve required generic constraints, variance, overload resolution, nullable annotations, pattern-matching semantics, and public signature compatibility.
- Do not replace a clear domain type with primitive values merely to reduce declarations. Conversely, do not retain wrapper types that carry no invariant, behavior, identity, or compatibility value.

## Dynamic behavior and reflection

- Trace `dynamic`, reflection, expression trees, late binding, service location, generated members, and string-based lookup to their real consumer before proposing removal.
- Contain unavoidable dynamic behavior behind a small typed boundary with explicit failure behavior and focused tests.
- Preserve justified uses in serializers, ORMs, dependency injection, UI binding, plugin systems, interop, source generators, compatibility shims, and framework discovery.
- Never rename or delete a member used through reflection or serialization without evidence that names, trimming behavior, and external consumers remain valid.

## Exceptions, async work, and ownership

- Reject broad catches, exception translation, retries, or defaults only when their actual semantics hide failure, discard cancellation, duplicate policy, or violate an established contract.
- Preserve exception filters, causal context, stack information, status mappings, and documented public exception behavior.
- Follow `async` and cancellation across the complete call path. Avoid sync-over-async, unobserved tasks, fire-and-forget work without a lifecycle owner, and cancellation tokens accepted but not meaningfully propagated.
- Check construction and disposal together for `IDisposable`, `IAsyncDisposable`, streams, locks, subscriptions, timers, scopes, and hosted services. Respect framework or container ownership; do not add disposal where the caller does not own the resource.
- Preserve dependency-injection lifetimes and per-request, per-session, or process-wide isolation. A shorter registration graph is not simpler if it introduces captive dependencies or shared mutable state.

## Abstraction and generated boundaries

- Remove interfaces, factories, adapters, or registries only after checking runtime selection, test seams, accessibility boundaries, generated consumers, and supported extension points.
- Prefer direct framework or standard-library capabilities when they fully preserve the repository's semantics. Do not add a new abstraction merely to replace an old one.
- Treat generated code, designer files, migrations, source-generator output, and vendored code as owned by their producer unless repository instructions say otherwise. Change the source or configuration, not generated residue.
- Do not use `#pragma`, analyzer configuration, nullable-context changes, or warning suppression as a substitute for establishing the invariant.

## Repository-native verification

Discover the SDK pin, target frameworks, solution or project graph, build properties, analyzers, test projects, and CI commands before selecting checks. When restore assets are already present, prefer targeted non-restoring commands such as `dotnet test --no-restore`, `dotnet build --no-restore`, or an existing non-rewriting analyzer invocation. Use `dotnet format --verify-no-changes --no-restore` only when it is already part of the repository workflow and its scope is understood. Treat missing restore assets or packages as a verification gap or `BLOCKED`; do not trigger a restore, and route a proposed dependency action through `$audit-dependencies`.

Compare before and after results for public API shape, nullable warnings, serialization, reflection or trimming behavior, async and disposal behavior, and affected tests. Do not install workloads, SDKs, analyzers, or packages to complete the task.

## Primary language references

- [Nullable reference types](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/null-safety/nullable-reference-types)
- [Null-forgiving operator](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/null-forgiving)
- [Using type `dynamic`](https://learn.microsoft.com/en-us/dotnet/csharp/advanced-topics/interop/using-type-dynamic)
- [Asynchronous programming scenarios](https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-scenarios)
- [Implementing `Dispose` and `DisposeAsync`](https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/implementing-disposeasync)
