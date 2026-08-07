# Content and Hierarchy

Write interface copy that helps users understand state, choose an action, and recover from problems. Remove repetition without erasing necessary context.

## Use page-header economy

A normal product-page header contains:

1. location context only when navigation does not already make it clear;
2. one semantic H1 naming the page or current object;
3. supporting text only when it changes understanding or action;
4. status or primary actions when they belong at page level.

Do not add a small uppercase category plus H1 plus generic subtitle by default. Test every line for information gain.

## Apply the information-gain test

Keep supporting text when it answers at least one consequential question:

- What is included or excluded?
- What source, owner, version, or time range applies?
- What is the current state or freshness?
- What consequence follows from an action?
- What prerequisite or limitation matters?
- What should the user do next?

Remove or rewrite text that merely restates the title, describes visible controls, uses promotional filler, or repeats nearby navigation.

## Preserve valid contextual elements

Do not force distinct information into an eyebrow treatment. Use the semantic pattern that matches it:

- breadcrumbs for hierarchy and location;
- step indicators for progress;
- badges or status text for state;
- metadata lists for owner, date, type, source, and timestamps;
- alerts for consequential warnings or required action;
- captions for figures, tables, and data provenance.

Detail pages may legitimately show compact metadata near the H1. Keep it when it helps identify, compare, or interpret the object.

## Maintain heading structure

- Use one H1 for the page's primary topic.
- Keep heading levels ordered by document structure, not visual size.
- Do not use bold paragraphs or styled spans as substitute headings.
- Let component headings describe the content or task, not the visual container.
- Ensure headings remain useful when read as an outline by assistive technology.

## Labels and helper text

- Name controls by the value or action they affect.
- Keep labels visible and persistent; use placeholders for examples only.
- Put units, formats, limits, and optionality where users encounter the input.
- Use helper text for non-obvious constraints, not to narrate standard controls.
- Keep terminology consistent with routes, domain models, help content, and existing user vocabulary.

## Buttons and links

- Begin action labels with a specific verb: "Save settings," "Export results," or "Delete account."
- Use links for navigation and buttons for actions.
- Match labels to the immediate outcome, especially for multi-step and destructive flows.
- Avoid several visually primary actions in one decision area.
- Give icon-only controls accessible names and ensure the icon is established or accompanied by help.

## Errors, confirmations, and status

- State what happened, what was affected, and how to recover.
- Do not blame the user or expose internal implementation details.
- Preserve entered work after recoverable failures.
- Make success messages specific enough to confirm the resulting state.
- Name destructive targets and consequences in confirmation UI.
- Keep long-running progress and final status discoverable after transient messages disappear.

## Empty and zero-result states

Differentiate:

- first-use empty state: explain the value and offer the next valid action;
- filtered zero results: show active constraints and a clear way to broaden or reset them;
- no permission: explain the boundary and available request or navigation path;
- unavailable or failed data: describe the failure and recovery without presenting it as emptiness;
- legitimate zero: show zero without implying missing data.

Do not invent sample records in production UI unless clearly marked and authorized.

## Editing test

For each changed string, verify:

- it adds information or enables action;
- it uses established product terms;
- it remains accurate across loading, error, empty, and permission states;
- it can expand for localization and large text;
- its accessible name and visible text do not conflict;
- tests, analytics, automation selectors, and help links remain valid.
