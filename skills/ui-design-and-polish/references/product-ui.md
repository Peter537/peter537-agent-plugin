# Product UI

Use these principles for task-oriented software: dashboards, data tools, forms, settings, workflows, and application shells. Optimize for comprehension, control, and reliable completion before decoration.

## Start from the task

- Identify the primary user job, the decision or action the screen supports, and the information needed at that moment.
- Put the primary task and its current state ahead of explanatory or promotional material.
- Match density to the work. Operational and data-heavy interfaces often need compact, scan-friendly layouts; unfamiliar or high-risk workflows need more guidance and spacing.
- Preserve stable placement for navigation and recurring actions. Do not make frequent users rediscover the interface after a cosmetic change.
- Use progressive disclosure for secondary detail, not to hide required context or basic controls.

## Establish hierarchy

- Give each page one semantic H1 and one visually dominant purpose.
- Make the primary action clear without styling every action as primary.
- Group by task and relationship. Avoid using cards as the default wrapper for every piece of content.
- Prefer alignment, spacing, typography, and dividers before adding nested containers, shadows, gradients, or borders.
- Keep the reading and action order consistent with DOM and keyboard order.
- Use whitespace to clarify groups, not to make operational interfaces unnecessarily sparse.

## Navigation and application shells

- Use navigation labels that describe destinations in product language.
- Expose location through the appropriate mechanism: active navigation, breadcrumb, page title, or step indicator.
- Keep global, section, page, and row-level actions visually distinct.
- Preserve deep links, back behavior, browser history, query state, and selected context.
- Collapse or adapt navigation deliberately on smaller screens; do not merely hide essential destinations.

## Forms and workflows

- Use visible labels. Placeholder text may provide an example but must not be the only label.
- Group related inputs with meaningful headings or fieldsets.
- Put help before the error it can prevent; put error text next to the field and provide a useful summary for complex forms.
- Explain format, units, optionality, irreversible effects, and prerequisites where ambiguity is costly.
- Disable submission only when it improves safety and remains understandable. Prevent duplicate actions and communicate pending state.
- Preserve entered values after recoverable validation or server failures.
- Require confirmation for destructive actions when the consequence is significant; name the object and consequence.

## Tables and data-heavy layouts

- Use tables for comparable records and aligned fields; do not replace them with card grids solely for appearance.
- Preserve headers, units, formatting, sort direction, filters, pagination, and selection state.
- Keep row actions discoverable by keyboard and touch, not hover alone.
- Prioritize the columns needed for the primary decision. Allow horizontal scrolling or responsive detail views rather than compressing content beyond readability.
- Distinguish zero values from missing, unavailable, loading, and error states.
- Show data source, freshness, timezone, scope, or calculation rules when they affect interpretation.
- For charts, include a text equivalent or accessible data view and never rely on color alone.

## Actions and feedback

- Use verbs that predict the result. Reserve generic labels such as "Continue" for genuinely linear flows.
- Keep primary actions few and context-specific. Style secondary, tertiary, destructive, and navigation actions according to consequence.
- Show immediate feedback for user actions and durable status for background or long-running work.
- Do not use toast messages as the only record of an important failure or irreversible change.
- Keep hit areas and focus behavior intact when creating icon-only actions; provide accessible names and visible tooltips where helpful.

## Tokens and shared components

- Inventory existing colors, type scales, spacing, radii, borders, shadows, motion, icons, and components before adding variants.
- Prefer semantic tokens such as surface, text-muted, danger, and focus over page-specific literal values.
- Reuse existing component contracts. Extend them only when a repeated product need is demonstrated.
- Avoid parallel styling systems, one-off arbitrary values, and near-duplicate components.
- Confirm light and dark themes where both are supported; do not assume token inversion preserves contrast or hierarchy.

## Responsive composition

- Reflow according to task priority rather than shrinking the desktop layout.
- Keep primary actions and current state visible at narrow widths.
- Allow controls to wrap in a predictable order and keep labels attached to inputs.
- Test long navigation labels, localized strings, validation messages, dense data, and system text scaling.
- Avoid fixed dimensions unless the contained data or interaction truly requires them.
