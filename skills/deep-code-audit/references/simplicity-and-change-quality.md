# Simplicity and Change-Quality Review

Use this reference to determine whether an implementation or change adds unnecessary behavior, concepts, indirection, dependencies, operational obligations, or unrelated edits. This method supplements correctness, security, testing, architecture, and operations; simplicity never overrides them.

## Contents

- Define the total surface
- Establish required behavior
- Trace the real path
- Inventory implementation and patch surface
- Apply the necessity ladder
- Test necessity counterfactually
- Investigate accidental-complexity patterns
- Require a demonstrated abstraction benefit
- Compare lifetime costs
- Preserve readability and necessary explicitness
- Review generated changes without authorship bias
- Apply the finding threshold
- Summarize change quality qualitatively

## Define the total surface

Treat simplicity as the least total conceptual and operational machinery that completely and clearly satisfies evidenced behavior and constraints. Count consequences across:

- reviewed code, callers, and consumers;
- public contracts and compatibility promises;
- state, data, persistence, and migrations;
- tests, fixtures, and tooling;
- dependencies, builds, and generated inputs;
- configuration and secrets;
- deployment, monitoring, support, recovery, and removal;
- security, privacy, accessibility, and other required controls.

Distinguish four concerns:

- Essential complexity comes from the domain, protocol, compatibility contract, security model, distributed behavior, hardware, regulation, or required user experience.
- Accidental complexity comes from the chosen representation, speculative behavior, duplicated policy, unsuitable abstractions, unnecessary state, or parallel mechanisms.
- Patch complexity is the review, rollback, and causal risk created by unrelated or diffuse edits.
- Lifecycle complexity is the continuing update, migration, deployment, monitoring, security, support, and removal burden.

A shorter local implementation is not simpler when it hides essential behavior or moves more complexity into another boundary.

## Establish required behavior

Before proposing deletion or consolidation:

- identify requested and currently promised behavior;
- inspect callers, tests, schemas, documentation, configuration, and relevant history;
- establish supported environments and compatibility commitments;
- identify trust, privilege, process, network, filesystem, persistence, and lifecycle boundaries;
- include required failure, recovery, cancellation, migration, and rollback behavior;
- distinguish product policy from an implementation accident.

If intent cannot be established, mark the question `research-gated`. Reviewer uncertainty is not evidence that behavior is unnecessary.

## Trace the real path

Trace the applicable flow through entry, validation, authorization, transformation, state change, side effects, errors, retries, cleanup, output, callers, and sibling entrypoints. Determine where each invariant and policy belongs.

A local guard may protect a distinct trust boundary, or it may duplicate policy that belongs upstream. A shared correction may need several callers, tests, schemas, or generated outputs to change together. Judge coherence by behavior and ownership, not file count.

## Inventory implementation and patch surface

For a change audit, compare the base and reviewed states. For a repository audit, compare the current design only with plausible alternatives supported by repository evidence.

Record material additions or changes in:

| Surface | Questions |
| --- | --- |
| Behavior | Was required behavior added, removed, broadened, or guessed? |
| Patch | Are unrelated formatting, renames, generated output, debug residue, or refactors mixed in? |
| Concepts | Which domain terms, policies, abstractions, and ownership rules must readers learn? |
| Control flow | Which states, modes, branches, callbacks, retries, or asynchronous paths were added? |
| Indirection | Which wrappers, factories, adapters, registries, interfaces, or tracing hops were added? |
| Public surface | Which APIs, schemas, commands, events, types, or compatibility promises became observable? |
| Dependencies | Which packages, plugins, actions, images, generators, or services were added? |
| Configuration | Which options, defaults, secrets, precedence rules, and invalid combinations were introduced? |
| Data | Which storage, caches, indexes, migrations, synchronization, retention, or cleanup duties were added? |
| Operations | Which processes, jobs, queues, alerts, deployment steps, or rollback paths were added? |
| Security | Which input, privilege, network, filesystem, process, tenant, or data boundary changed? |
| Verification | Which tests, fixtures, mocks, setup, and ongoing maintenance were added or omitted? |

Use this inventory to expose complexity transfers. Do not convert it into a numeric score.

## Apply the necessity ladder

Consider the first fully adequate option:

1. Clarify whether the behavior and its necessity are evidenced.
2. Avoid adding behavior or machinery when the requirement can be met without it.
3. Delete or consolidate behavior that is proven obsolete, duplicated, or guaranteed at the correct boundary.
4. Reuse a correct, maintained, and appropriately coupled repository capability.
5. Use a language or standard-library feature that handles required semantics and supported runtimes.
6. Use a native platform or framework facility that fits lifecycle, security, and compatibility needs.
7. Reuse an already-installed dependency when its existing use and total cost are suitable.
8. Write a small direct implementation without speculative generality.
9. Add a new abstraction, dependency, service, subsystem, or framework only when its lifetime benefit is demonstrated.

This is a decision aid, not an absolute order. Existing helpers may have incorrect semantics, low-level primitives may be unsafe for complex standards, maintained dependencies may be safer than handwritten code, and adapters may be justified at volatile or privileged boundaries.

## Test necessity counterfactually

For every material concept or edit, ask what evidenced behavior, invariant, compatibility promise, or operational property would fail if it were absent. A concrete answer supports necessity; no answer creates a candidate for investigation, not automatic deletion.

Also check:

- whether another boundary already provides the behavior;
- whether the need is current or speculative;
- whether dynamic callers, external consumers, registration, generation, packaging, migrations, or operations are invisible to static search;
- whether removal transfers complexity or risk elsewhere;
- whether the alternative is clearer to its future owner;
- whether existing or proposed checks can distinguish the designs.

The audit is read-only. Describe a safe verification procedure rather than deleting or rewriting code experimentally.

## Investigate accidental-complexity patterns

Treat these as hypotheses that require context and consequence:

- future variants, extension points, modes, flags, or fallback paths without an evidenced consumer;
- forwarding wrappers, single-implementation factories, pass-through layers, staged builders, or type hierarchies without a real boundary or valid-state benefit;
- shared abstractions governed by expanding mode flags or callers with materially different policy;
- repeated validation, authorization, normalization, serialization, retry, or recovery policy that lacks one owner;
- custom implementations of adequate repository, language, platform, framework, or dependency behavior;
- symptom guards repeated across callers instead of a shared root-cause correction;
- caches, stored derived values, asynchronous work, queues, locks, schedulers, or persistent schema without a demonstrated workload and lifecycle;
- unused imports, values, types, files, dependencies, configuration, scratch scripts, debug output, placeholders, commented alternatives, or obsolete compatibility paths;
- tests that mirror implementation, cannot fail meaningfully, duplicate the same boundary, or require disproportionate mocks and fixtures;
- comments or documentation that restate syntax while omitting the actual constraint or trade-off.

Similar syntax does not prove shared responsibility. A single-use abstraction can still protect a public, platform, security, lifecycle, generated-code, compatibility, or nondeterministic boundary.

## Require a demonstrated abstraction benefit

An abstraction is justified when evidence demonstrates one or more material benefits for the reviewed context. Examples include naming a coherent concept or policy, protecting a meaningful boundary, centralizing behavior that must remain consistent, reducing total decisions or coupling, giving consumers a smaller misuse-resistant contract, or supporting real variation. Its ownership and likely evolution must still be understandable.

Do not recommend an abstraction because code can be extracted, a pattern has a name, a future implementation might exist, mocking becomes convenient, or two fragments share syntax without shared policy. When a shared abstraction is demonstrably unstable, temporarily explicit duplication may reveal the actual variation more safely than another flag.

## Compare lifetime costs

When comparing direct code, an existing dependency, and a new dependency, include correctness, standards edge cases, security history, update path, ownership, transitive and install surface, runtime cost, native code, scripts, permissions, licensing, API stability, observability, test burden, and migration or removal cost.

Do not replace mature cryptography, authentication, authorization, protocol, serialization, archive, parser, Unicode, date/time, or security libraries with handwritten code merely to reduce package count. Do not add a dependency to avoid a small, obvious, stable, non-security-sensitive implementation when the package has greater lifetime cost.

## Preserve readability and necessary explicitness

Never optimize for one line, minimum characters, minimum functions, minimum files, maximum function size, or maximum abstraction count. Prefer explicit domain terms, visible invariants and units, unsurprising control flow, clear side effects, bounded state, and cohesive ownership.

Do not simplify away validation, authentication, authorization, tenant isolation, data-loss protection, cleanup, transactions, timeouts, cancellation, backpressure, accessibility, localization, cryptographic behavior, compatibility periods, migration, rollback, recovery, synchronization, resource limits, or actionable operational evidence.

## Review generated changes without authorship bias

Do not determine authorship from style, call a finding AI-generated without established relevance, or alter classification because an AI tool was used. Apply the same observable checks to every change, with additional attention to broad generated patches:

- unrelated hunks and overwrite of established structure;
- duplicated helpers or policy;
- unsupported packages, APIs, flags, versions, or configuration;
- hidden undeclared runtime requirements;
- debug residue, placeholders, scratch artifacts, and shallow tests;
- broad exception handling and silent fallback;
- security-sensitive logic without applicable authoritative guidance;
- copied code with licensing, vulnerability, or maintenance implications;
- nondeterministically generated artifacts without reproducible sources.

A successful build or test suite proves only the exercised behavior. An author's claim that a change is minimal is not evidence of necessity.

## Apply the finding threshold

Report a simplicity or change-quality finding only when the audit can establish:

1. required behavior and constraints;
2. the exact unnecessary or misplaced surface;
3. a concrete reader, correctness, security, operational, performance, compatibility, or maintenance cost;
4. a simpler behaviorally complete alternative;
5. evidence supporting equivalence;
6. trade-offs and complexity transfers;
7. a regression-sensitive verification method.

If required behavior, an adequate alternative, or equivalence evidence is missing, make the question `research-gated`, optional, or omit it. Do not report a finding solely from length, file count, duplication, one implementation, few call sites, generic metric thresholds, or style that appears machine-generated.

## Summarize change quality qualitatively

For a scoped change, summarize only when useful:

- Resulting complexity: `reduced`, `materially unchanged`, or `increased`.
- Added-surface justification: `evidenced`, `partly evidenced`, or `unproven`.
- Patch focus: `focused`, `mixed`, or `diffuse`.
- Verification: `strong`, `partial`, `weak`, or `blocked`.

Explain the basis briefly and do not combine these into a numeric score. For a whole repository, report demonstrated systemic patterns and representative locations rather than inventing an ideal minimal rewrite.

## Method sources

Use these sources as methods, not universal thresholds:

- [Google Engineering Practices: What to look for in a code review](https://google.github.io/eng-practices/review/reviewer/looking-for.html) for design, complexity, tests, and fact-based review.
- [Google Engineering Practices: Small changes](https://google.github.io/eng-practices/review/developer/small-cls.html) for conceptually coherent, self-contained changes rather than line-count minimalism.
- [On the Criteria To Be Used in Decomposing Systems into Modules](https://doi.org/10.1145/361598.361623) for decomposition around changeable design decisions and information hiding.
- [No Silver Bullet](https://doi.org/10.1109/MC.1987.1663532) for the distinction between essential and accidental complexity.
- [Expectations, Outcomes, and Challenges of Modern Code Review](https://www.microsoft.com/en-us/research/publication/expectations-outcomes-and-challenges-of-modern-code-review/) for review as code and change understanding, defect discovery, and knowledge transfer.
- [The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction) as practitioner guidance on conditional accumulation and the potential value of explicit duplication.

These instructions are original. Do not copy source prose, examples, scoring systems, or branded rules into an audit report.
