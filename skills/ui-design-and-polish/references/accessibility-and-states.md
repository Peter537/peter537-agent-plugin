# Accessibility and States

Use [WCAG 2.2](https://www.w3.org/TR/WCAG22/) Level AA as the review baseline. A normal code and browser pass can identify and correct issues but cannot establish formal conformance by itself.

## Semantics and structure

- Use native HTML and framework controls before custom interaction patterns.
- Preserve landmarks, ordered heading structure, lists, tables, form relationships, and meaningful reading order.
- Give controls programmatic names that agree with visible labels.
- Associate instructions and errors with their controls.
- Mark decorative imagery appropriately and provide useful alternatives for informative imagery.
- Announce important asynchronous state changes without moving focus unexpectedly.

## Keyboard and focus

- Make every interactive function reachable and operable with a keyboard.
- Keep focus order aligned with the visual and task order.
- Show a visible focus indicator with sufficient contrast.
- Ensure sticky headers, overlays, cookie banners, and drawers do not obscure focused elements.
- Move focus only when the interaction creates a new task context, such as a dialog; restore it predictably on close.
- Provide an efficient way past repeated navigation where applicable.
- Avoid keyboard traps and hover-only controls.

## Visual perception

- Verify text, controls, focus indicators, charts, and state indicators against applicable contrast requirements.
- Do not communicate status or required action by color alone.
- Preserve meaning at 200% text zoom and under browser reflow; avoid clipped labels, hidden actions, and overlapping content.
- Support high text density without reducing legibility or target usability.
- Keep essential touch and pointer targets large enough for reliable operation; inspect spacing between adjacent targets.

## Motion and timing

- Respect `prefers-reduced-motion` and framework equivalents.
- Use motion to explain state or spatial change, not merely to decorate.
- Avoid unexpected autoplay, looping distraction, and interaction that depends on animation completion.
- Provide control over time limits, auto-updates, and moving content when relevant.

## Forms and authentication

- Provide visible labels, clear requirements, field-level errors, and a useful error summary for complex forms.
- Retain user input after validation failures.
- Do not block password managers, paste, or accessible authentication methods without a security requirement.
- Explain required format before submission when possible.
- Make destructive or consequential actions reversible or confirmable when appropriate.

## Assistive-technology checks

Use the accessibility tree or DOM when available to inspect names, roles, states, descriptions, live regions, table associations, and hidden content. Automated rules support the review but do not replace keyboard use, focus inspection, content judgment, or representative screen-reader testing.

## State matrix

For every applicable surface, determine its content, available actions, focus behavior, announcement behavior, and recovery path in these states:

| State | Questions to answer |
| --- | --- |
| Loading | Is progress perceivable, is prior content handled honestly, and are duplicate actions prevented? |
| Empty | Is this first use, a valid absence, or missing data, and is the next action clear? |
| Zero results | Are filters and scope visible, and can the user reset or broaden them? |
| Error | What failed, what remains safe, and how can the user retry or recover? |
| Success | What changed, where is the result, and does focus remain sensible? |
| Permission denied | What boundary applies, what can still be done, and who can grant access? |
| Stale or offline | Is freshness visible, are edits safe, and what happens on reconnect? |
| Destructive action | Is the target and consequence explicit, and is cancellation safe? |
| Long or localized content | Does text wrap, expand, truncate accessibly, and preserve controls? |
| Large dataset | Are loading, pagination, virtualization, selection, and announcements usable? |
| Light and dark themes | Do hierarchy, contrast, charts, and system states survive both themes? |
| Reduced motion | Is all information and functionality preserved without animation? |

## Verification evidence

Record which checks were automated, source-inspected, keyboard-tested, browser-inspected, or not run. Report unresolved issues by user consequence and affected route or state. Never state that the interface is accessible or WCAG-conformant solely because an automated scanner reports no violations.
