# Protected comments and native checks

Read this reference before editing any comment whose exact syntax, location, or content may be consumed outside the immediate reader. Treat uncertain protection as a reason to investigate, not as evidence that the comment is disposable.

## Identify protected surfaces

### Public API documentation

Documentation comments can be part of the published developer contract and an input to generated documentation. Inspect public/exported declarations, documentation configuration, build warnings, link targets, examples, inheritance rules, and downstream consumers. Descriptive what/how content may be required even when it resembles the signature.

Examples include Go doc comments and C# XML documentation. Follow the repository's language and framework convention; do not normalize all ecosystems to one format.

### Executable examples and doctests

Docstrings and documentation comments may contain examples executed by a test runner. Preserve prompt markers, expected output, hidden setup, feature gates, attributes, language fences, and exact whitespace when their runner depends on them.

Doctests execute code. Run them only when the repository already configures the command, the environment is safe, and execution is within the user's authorization. A passing parser or rendered page is not proof that the example was executed.

### Compiler, linter, formatter, and analyzer controls

Comments may suppress or configure diagnostics, coverage, formatting, type checking, bundling, tree shaking, code generation, or other tools. Determine:

- the exact consumer and configured version;
- the controlled line, block, file, declaration, or generated region;
- whether a paired enable/disable or start/end marker exists;
- the diagnostic or behavior that returns when the directive is removed;
- whether the directive remains necessary or can be narrowed safely.

Never remove a suppression merely because its explanation is weak. First reproduce the underlying diagnostic with the already-configured tool or classify the candidate as `investigate`. Do not broaden or add suppressions to make validation pass.

TypeScript's `// @ts-expect-error`, for example, intentionally fails when the following line no longer produces an error; changing its placement or replacing it with a different suppression changes the check. See the official [TypeScript 3.9 release notes](https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-9.html#ts-expect-error-comments).

### Generated-source boundaries

Markers such as generated-file headers, generator provenance, editable-region boundaries, and source-map or tooling annotations can control regeneration or reviewer behavior. Identify the generator and authoritative input. Do not edit generated output by default, and never remove a marker to make generated content appear hand-maintained.

### Legal, license, attribution, and provenance text

Copyright, license, attribution, notice, source, and provenance comments may carry legal obligations. Preserve exact text and placement unless the user explicitly authorizes legal-text work and repository evidence establishes the permitted change. Do not infer that an old year or unfamiliar attribution is obsolete.

Where used, the [SPDX specification](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/) defines machine-readable license expressions; repository or organizational policy still controls whether and how an identifier may be changed.

### Build, packaging, deployment, and operations

Comments can be parsed by build scripts, packaging tools, documentation extractors, deployment systems, test harnesses, shell conventions, or operational tooling. Search repository configuration and scripts for the exact marker before changing it. A comment may also preserve a non-machine-enforced rollback, ordering, ownership, or incident constraint; validate that knowledge with current operational evidence rather than assuming it is obsolete.

### Security, concurrency, units, and protocol constraints

These comments are not automatically machine-consumed, but their removal can erase the only visible explanation for a required invariant. Trace validation, threat boundaries, locks, memory ownership, units, precision, ordering, protocol specifications, and tests before deciding that clearer code makes the comment unnecessary.

## Distinguish comments from comment-shaped data

Do not edit comment syntax inside string literals, parser/tokenizer fixtures, snapshots, golden files, embedded source examples, templates, generated test input, documentation captures, or expected diagnostics as if it were a source comment. Establish the containing language and consumer first. If parsing support is unavailable, sample conservatively and record the gap.

## Select repository-native checks

Use the smallest already-configured checks that exercise the comment's actual consumer. Inspect the command before running it; test and documentation commands can execute arbitrary repository or example code.

| Surface | Useful existing evidence | Possible already-configured check |
| --- | --- | --- |
| Go documentation and examples | Exported declarations, examples, package docs | Repository `go test` or documentation checks |
| Rust documentation | Rustdoc attributes, code fences, crate features | Repository `cargo test --doc` with required feature variants |
| Python docstrings and doctests | `doctest` configuration, test collection, expected output | Repository test target or explicitly configured doctest command |
| C# XML documentation | Project properties, warning configuration, generated XML | Existing `dotnet build` or documentation target |
| TypeScript directives | `tsconfig`, compiler version, project references | Existing type-check or build target |
| Linter/formatter suppressions | Tool configuration and diagnostic identifier | Existing non-rewriting lint or format-check target |
| Generated markers | Generator configuration and authoritative inputs | Existing generator check or clean regeneration in an isolated disposable location |
| Build or packaging annotations | Scripts that parse the marker, matrix variants | Existing dry-run or verification target for the affected variant |

These are categories, not universal commands. Respect repository instructions, pinned versions, workspaces, build variants, environment requirements, and authorization. Do not install missing dependencies, download toolchains, run auto-fix modes, regenerate tracked files, start external services, or execute untrusted examples merely to validate a comment.

## Interpret results conservatively

- Passing one check proves only the exercised consumer and configuration.
- A directive that no longer changes one build may still serve another target, workspace, version, or platform.
- A clean documentation build does not establish that prose is truthful.
- Failure after removal is strong evidence of a protected behavior; restore the original and narrow the proposed action.
- Inability to run a check is a coverage gap. Preserve the comment or request a maintainer decision rather than presenting removal as safe.

Official documentation for protected documentation-test behavior includes [Rust documentation tests](https://doc.rust-lang.org/rustdoc/write-documentation/documentation-tests.html) and [Python's `doctest` module](https://docs.python.org/3/library/doctest.html).
