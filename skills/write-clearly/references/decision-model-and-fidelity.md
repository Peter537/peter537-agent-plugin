# Decision model and fidelity

Use this reference to decide what may change and how to preserve the source's meaning.

## Authority order

Apply constraints in this order:

1. Safety, factual fidelity, protected material, and legal requirements.
2. The current user's explicit instruction.
3. Exact human edits and already accepted feedback.
4. Repository or organization terminology and style guidance.
5. Representative samples from the same author, language, and genre.
6. The selected document and style profile.
7. Generic reader-first defaults.

When sources at the same level conflict, preserve the existing wording and report the ambiguity. Do not select whichever wording appears smoother.

## Editing intensities

- **Proofreading:** correct requested spelling, punctuation, grammar, and obvious mechanical mistakes. Do not recast sound sentences.
- **Light copyedit:** improve local clarity, consistency, and flow without changing paragraph purpose or order.
- **Standard rewrite:** recast paragraphs and sentences, remove unnecessary material, and reorganize locally while preserving the established content model.
- **Structural rewrite:** move, merge, split, add, or remove sections when the user authorized content and structure changes.

Default to the lowest intensity that meets the request. A narrow request such as “fix spelling only” remains narrow even when this skill activates implicitly.

## Fidelity dimensions

### Literal fidelity

Preserve names, numbers, dates, units, prices, versions, citations, URLs, quotations, code, commands, identifiers, flags, paths, UI labels, placeholders, and approved terminology unless the request explicitly targets them.

### Logical fidelity

Preserve negation, modality, conditions, exceptions, dependencies, comparisons, sequence, causality, and scope. Watch for small edits that change the proposition:

- possibility versus certainty;
- recommendation versus requirement;
- default behavior versus universal behavior;
- one example versus an exhaustive set;
- correlation versus cause;
- current support versus future intent.

### Epistemic fidelity

Keep verified, estimated, alleged, proposed, uncertain, observed, recommended, and opinion statements distinct. Do not remove a hedge when evidence requires it or add a hedge that weakens an established requirement.

### Attribution and completeness

Keep claims attached to their actual source or speaker. Preserve prerequisites, warnings, exceptions, limitations, and steps that a reader needs even when they interrupt the rhythm.

## Drafting factual prose

Use the user's brief and repository evidence as the content boundary. If a fact, benefit, example, metric, decision, or source is unavailable, ask, omit it, or mark the gap outside the drafted prose. Do not manufacture a plausible value or insert an unapproved placeholder into a tracked file.

## Conflict and stop conditions

Stop or request direction when:

- a proposed improvement changes product behavior or policy rather than describing it;
- style guidance conflicts with a safety warning or required legal phrase;
- author samples conflict materially with the requested audience or house standard;
- structural editing would remove unique information without an authorized destination;
- the source language or intended locale cannot be established well enough to edit safely;
- high-risk ambiguity cannot be resolved from authoritative material.
