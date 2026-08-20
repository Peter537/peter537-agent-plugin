# Liveness, Entrypoints, and Tool Evidence

Use this reference to establish what can reach a proposed removal. Build a repository-specific liveness model before accepting analyzer output.

## Map the executable and distributable system

Inventory the parts of the repository that can make code or assets live:

- application, service, worker, command, library, test, benchmark, example, migration, generator, and packaging entrypoints;
- workspace and project boundaries, build scripts, CI jobs, release packaging, deployment manifests, and platform-specific projects;
- public exports, published packages, extension points, plugins, generated SDKs, templates, embedded resources, static assets, and native bindings;
- supported operating systems, architectures, target frameworks, feature sets, editions, locales, and debug or release configurations.

Derive the supported variant set from repository evidence rather than inventing an exhaustive cross-product. CI matrices, release scripts, package metadata, documented support policy, and recent releases are stronger evidence than a developer's default local build.

## Establish entrypoints and consumers

Trace both direct and indirect consumers:

- ordinary imports, calls, references, inheritance, interface implementation, type constraints, and event wiring;
- route, command, job, serializer, dependency-injection, test, fixture, and framework discovery;
- reflection, annotations or attributes, decorators, dynamic imports, string-based lookup, registry tables, service loaders, and plugin manifests;
- filenames, directory conventions, resource names, CSS selectors, templates, localization keys, and configuration keys interpreted by tools or frameworks;
- side-effect imports, module or type initializers, registration-only code, and code reached only during startup, shutdown, recovery, migration, or failure handling;
- public APIs, package exports, scripts, samples, downstream repositories, user configuration, generated consumers, and compatibility contracts outside the current checkout.

A declaration with no internal caller may still be a public contract. A file with no import may still be convention-loaded. A branch with no ordinary test may still protect recovery, security, upgrade, or platform behavior.

## Treat generated surface in both directions

- Identify generated outputs by repository conventions and generation markers; then locate their source schemas, templates, or generators.
- Do not edit generated output as the authoritative removal when it will be recreated.
- Do not classify a generator input as unused merely because the generated consumer is absent before a build.
- If safe generation is already part of the repository workflow, use its documented non-deploying verification path. Do not run untrusted generators or install missing tooling.
- When generated inputs or outputs are unavailable, record the affected conclusion as `research-gated`.

## Use tools as scoped evidence

Prefer already-configured repository-native compilers, linters, analyzers, tests, coverage tools, linkers, and packaging checks. Record the exact configuration each result describes.

- A static reachability result describes the tool's entrypoint model, language features, plugins, generated inputs, and build configuration. Inspect its documented blind spots before promoting a finding.
- A compiler or linker warning can support a candidate but does not establish product obsolescence, public-consumer absence, or safe operational retirement.
- Search all relevant symbol spellings, serialized names, route names, identifiers, aliases, and generated forms. A negative text search is supporting evidence only.
- Tests show exercised contracts, not the complete consumer set. A test-only reference may mean the test is stale, but it may also expose a missing production registration or preserved public behavior.
- Runtime traces and telemetry show liveness for observed inputs, environments, and time windows. They cannot prove absence elsewhere.
- History can explain why a surface exists and whether an announced deprecation or replacement completed. Age and low churn are not evidence of death.

Do not change tool configuration or add ignore rules merely to obtain a cleaner report. A surprising tool result can identify either dead surface or a missing entrypoint/configuration model; resolve which one applies.

## Classification checks

Use `ready` only when all material questions have defensible answers:

1. Which supported entrypoints and variants were evaluated?
2. What static, dynamic, generated, and convention-based consumers were checked?
3. Is the surface exported, serialized, reflected, registered, or externally consumed?
4. Does initialization or cleanup produce required side effects?
5. Is the behavior intentionally reserved for compatibility, security, recovery, diagnostics, or future rollout already committed by the product?
6. Which existing check will distinguish a complete removal from a broken contract?

If a material answer is unknown, use `needs-decision` for an owner or policy choice and `research-gated` for missing technical evidence.

## Primary references

Accessed 2026-08-20.

- [Go `deadcode` command](https://pkg.go.dev/golang.org/x/tools/cmd/deadcode) documents entrypoint-based reachability, generated-code handling, configuration-specific results, and cases that still require judgment.
- [.NET trimming guidance](https://learn.microsoft.com/en-us/dotnet/core/deploying/trimming/prepare-libraries-for-trimming) explains reflection-sensitive analysis, annotations, dependency visibility, target-framework variants, and test-app coverage.
- [Knip issue handling](https://knip.dev/guides/handling-issues) documents entry-file modeling, generated sources, dynamic imports, framework plugins, workspaces, and configuration gaps.
- [Python `importlib`](https://docs.python.org/3/library/importlib.html) is the language reference for runtime import machinery and custom finders or loaders.
- [GitHub Actions matrix jobs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations) describes repository-declared build and test variants that may change liveness.
