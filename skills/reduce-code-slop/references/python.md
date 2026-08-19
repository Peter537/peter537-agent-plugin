# Python Simplification Guidance

Use this reference only for Python work. Type annotations and static-checker results are evidence about declared intent; they do not enforce runtime behavior by themselves.

## Type evidence and boundaries

- Trace `Any`, `typing.cast`, ignored type errors, broad mappings, and attribute probing to the boundary where uncertainty enters.
- `typing.cast()` returns its input unchanged at runtime. Replace cast laundering only when the repository can express or validate the real invariant without changing supported inputs.
- Validate external JSON, configuration, environment data, database rows, plugin values, deserialized objects, and third-party responses at a clear boundary. Reuse an already-adopted validation or model mechanism rather than introducing a package.
- Prefer precise protocols, typed mappings, data classes, enums, or domain types when they encode behavior that callers rely on. Do not create types that merely rename a primitive or mapping without adding an invariant or useful interface.
- Preserve runtime annotation consumers, forward-reference behavior, decorator metadata, descriptor semantics, and serialization field names.

## Dynamic behavior

- Inspect actual consumers before changing `getattr`, `setattr`, dynamic imports, registries, decorators, descriptors, metaclasses, monkeypatching, or framework discovery.
- Contain unavoidable dynamic behavior behind a small, explicit boundary with clear failure semantics and focused tests.
- Treat `eval` or `exec` as a security and behavior boundary, not a style issue. Do not replace it speculatively without understanding the accepted language and caller contract.
- Preserve justified dynamic patterns in ORMs, serializers, plugin systems, scientific or tabular workloads, dependency injection, test doubles, and framework hooks.

## Exceptions, async work, and resources

- Investigate broad catches and default-return fallbacks for hidden failure, lost context, swallowed cancellation, or mixed policy. Preserve intentionally supported sentinel or partial-result contracts.
- Keep exception chaining, domain error types, caller-visible messages, retry behavior, and cleanup semantics when they form part of the contract.
- Trace coroutine, task, future, and async-generator ownership. Preserve cancellation and exception observation; do not turn structured work into orphaned background tasks for brevity.
- Use existing context managers and lifecycle hooks for files, streams, locks, sessions, clients, transactions, generators, and temporary state. Check both normal and exceptional cleanup.
- Avoid replacing scoped state with module globals or implicit caches unless process-wide ownership is established and safe.

## Abstraction, tests, and enforcement

- Remove wrappers, factories, protocols, adapters, or registries only after checking runtime selection, alternate implementations, test seams, and downstream imports.
- Prefer a direct standard-library or already-adopted repository capability when it preserves semantics. Do not introduce a generic helper for one use or collapse distinct policies solely to reduce functions.
- Keep mocks at stable external boundaries. Do not simplify production code around an artificial test seam or weaken assertions to accommodate a refactor.
- Treat generated clients, migrations, vendored code, notebooks, and framework-generated artifacts according to their producer and repository policy.
- Do not add `# type: ignore`, linter exclusions, blanket exception annotations, or tool configuration merely to make enforcement green.

## Repository-native verification

Discover supported Python versions, environment and lock configuration, package layout, test runner, type checker, linter, formatter, and CI commands first. Use only already-installed, non-installing checks such as the repository's targeted `unittest` or `pytest` path, configured mypy or Pyright command, or configured Ruff check. Avoid formatter modes that rewrite files unless their exact scope is authorized, and remove task-created caches or artifacts without disturbing pre-existing ones.

Compare before and after behavior for imports, public call signatures, accepted data shapes, exceptions, async cleanup, serialization, and runtime annotation consumers. Do not create an environment, restore dependencies, or install a missing checker merely to complete the task.

## Primary language references

- [Python typing documentation](https://docs.python.org/3/library/typing.html)
- [Python data model](https://docs.python.org/3/reference/datamodel.html)
- [Coroutines and tasks](https://docs.python.org/3/library/asyncio-task.html)
- [Context-manager utilities](https://docs.python.org/3/library/contextlib.html)
