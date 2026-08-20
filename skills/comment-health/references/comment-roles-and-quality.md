# Comment roles and quality

Use this reference to decide what a comment contributes and whether to keep, rewrite, move, remove, narrow, or add it. A comment is healthy when its content, location, audience, and maintenance owner match the repository behavior it represents.

## Determine the role before judging the prose

| Role | Evidence to inspect | Typical healthy form | Common failure |
| --- | --- | --- | --- |
| Public contract | Exported declaration, compatibility promises, generated API documentation, callers | Accurate behavior, parameters, return values, errors, units, preconditions, and examples at the declaration | Restates an old signature, omits a material condition, or promises behavior the implementation does not provide |
| Usage or procedure | Supported calling sequence, tests, examples, framework requirements | Concrete what/how guidance needed to use the surface correctly | Narrates obvious syntax or preserves an obsolete procedure |
| Rationale or trade-off | Decision history, alternatives, issue or design record, current constraint | Explains a non-obvious choice and the condition that keeps it valid | Gives folklore without evidence or describes a constraint that no longer exists |
| Invariant or safety constraint | State model, concurrency and ownership rules, validation, tests | States the condition, boundary, and consequence that code alone cannot make obvious | Drifts from behavior or uses vague warnings that cannot guide a change |
| Algorithm, domain, or unit explanation | Formula, protocol, standard, data source, type and test evidence | Names the model, unit, coordinate system, ordering, precision, or non-obvious transformation | Merely translates each expression into English or uses stale terminology |
| Compatibility or operational boundary | Supported versions, migration policy, deployment and rollback behavior | Records the consumer and retirement condition | Becomes a permanent excuse without an identifiable consumer or exit condition |
| Task marker | Issue tracker, owner, condition, current work state | Specific unresolved work with enough context to verify or retire it | Vague TODO/FIXME text, completed work, or an inaccessible reference with no local meaning |
| Documentation test or example | Test runner and documentation configuration | Executable example aligned with public behavior | Appears decorative but fails, runs unsafe work, or demonstrates obsolete behavior |
| Tool control or generated/legal marker | Compiler, linter, formatter, generator, build, license, or provenance configuration | Exact syntax and placement required by the consumer | Treated as ordinary prose and reformatted or removed |
| Commented-out implementation | History, build variants, fixtures, feature controls | Rarely justified; retained only with a current, explicit reason and owner | Acts as informal version control or is mistaken for fixture/example data |
| Local narration | Nearby names, control flow, complexity, reader needs | Clarifies a dense transition or surprising language/framework behavior | Repeats readable code line by line and creates a second maintenance surface |

"Why" is often valuable, but it is not a universal replacement for "what" or "how." Public APIs, commands, protocols, procedures, units, and formats may need exact descriptive material. Conversely, rationale without a current constraint or evidenced decision can be less useful than a precise contract.

## Apply the five evidence dimensions

### Current truth

Compare the comment with source, tests, public interfaces, configuration, supported versions, and current repository terminology. Use history to understand intent, not to override present behavior. A contradiction is a candidate for investigation until the authoritative source is established; do not silently make the comment match whichever artifact was read first.

### Maintenance value

Identify the reader or tool and the error, uncertainty, or search cost the comment prevents. A comment may be valuable even when the code is locally readable if it records a cross-cutting invariant, external rule, unit, compatibility condition, or operational consequence. A comment that merely repeats a name is not automatically harmful; remove it only when doing so reduces maintenance surface without losing necessary context.

### Placement and abstraction

Keep knowledge near the decision or contract it governs and at the narrowest level that remains authoritative. Move system-wide policy out of a local implementation comment when a maintained architectural or operational source owns it. Do not move public API requirements away from the declaration if documentation tooling and consumers need them there.

### Best carrier

Prefer executable or structurally enforced carriers when they represent the knowledge more reliably: clearer names, types, validation, tests, declarative configuration, or generated documentation. This is not permission for comment-only work to refactor code. Use `refactor-required`, explain the proposed carrier and behavior to preserve, and leave executable changes for separately authorized work.

### Protection

Before editing, determine whether exact content or placement is consumed by legal policy, documentation generation, doctests, compilers, linters, formatters, build tools, release tooling, or operations. Read [protected-comments-and-native-checks.md](protected-comments-and-native-checks.md) when any such consumer is plausible.

## Choose an action

- `keep`: the comment is accurate, useful, well placed, and no safer carrier is justified.
- `rewrite`: the role and location are valid, but the content is misleading, incomplete, ambiguous, or needlessly difficult to maintain.
- `move`: the knowledge is useful but belongs beside a different declaration or in another authoritative maintained surface.
- `remove`: evidence shows that no required reader, behavior, or protected consumer would lose necessary information.
- `narrow`: retain the valid portion while removing an obsolete claim, excess scope, or overly broad directive.
- `add`: a demonstrated contract, invariant, safety constraint, unit, or non-obvious decision lacks an adequate carrier.
- `refactor-required`: code, types, tests, configuration, or architecture should become the authoritative carrier; do not perform that work under comment-only authorization.
- `investigate`: contradictory or incomplete evidence prevents a trustworthy decision.

Use `high` confidence only when repository evidence establishes the role, truth, consumers, and protection status. Use `medium` when the likely resolution is supported but a non-critical consumer or historical reason remains uncertain. Use `low` for a plausible concern that needs a maintainer decision or unavailable evidence; do not present it as a cleanup instruction.

## TODO and FIXME markers

Do not judge task markers from their age alone. Verify whether the condition remains, whether a referenced issue or owner is meaningful from available evidence, and whether the marker describes work more precisely than the code or test suite does.

- Keep or rewrite an active marker when it identifies a real limitation, desired end state, and useful verification or tracking context.
- Remove an explicitly approved marker when the work is demonstrably complete or the condition no longer exists.
- Use `investigate` for inaccessible references, ambiguous ownership, or a limitation that cannot be reproduced safely.
- Use `refactor-required` when deleting the marker would hide unfinished behavior rather than resolve it.

Do not access an external issue tracker or private system unless the user separately authorizes that destination and data flow.

## Commented-out material

First distinguish implementation from data. Comments can contain documentation examples, parser fixtures, language demonstrations, conditional configuration, or expected output. These are not dead code merely because they resemble code.

For actual commented-out implementation, inspect current callers, build variants, feature controls, history, and tests. Version control usually preserves removed implementation better than a stale block, but history availability alone does not establish that deletion is safe. Broad cleanup still requires a stable candidate and approval before removal.

## Primary guidance

- [Go doc comments](https://go.dev/doc/comment) defines documentation-comment conventions and their role in generated package documentation.
- [Python PEP 8: comments](https://peps.python.org/pep-0008/#comments) distinguishes useful, current comments from contradictory or obvious narration.
- [.NET XML documentation comments](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/xmldoc/) documents compiler-recognized source comments used to produce API documentation.
