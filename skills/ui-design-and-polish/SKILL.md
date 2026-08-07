---
name: ui-design-and-polish
description: Design, audit, refine, redesign, create, and polish product user interfaces using repository evidence and rendered verification. Use for dashboards, data tools, forms, settings, workflows, application shells, page hierarchy, UI copy, responsive behavior, accessibility, interaction states, design-system consistency, Streamlit interfaces, and Blazor Web Apps. Do not use for backend-only work, ordinary non-UI framework tasks, documentation-only changes, image-only work, or marketing, editorial, and commerce surfaces.
---

# UI Design and Polish

Improve product interfaces without losing product truth, framework behavior, or accessibility. Base decisions on repository evidence and the rendered application, not generic visual trends.

## Load the relevant guidance

Read the core references needed for the task before making design decisions:

- Read [product-ui.md](references/product-ui.md) for information architecture, density, layouts, actions, responsive composition, tokens, and component quality.
- Read [content-and-hierarchy.md](references/content-and-hierarchy.md) when changing headings, page introductions, labels, helper text, buttons, messages, or empty states.
- Read [accessibility-and-states.md](references/accessibility-and-states.md) for every audit or implementation that affects interaction, semantics, visual styling, or state handling.
- Read [visual-verification.md](references/visual-verification.md) whenever a rendered application may be inspected.
- Read exactly the detected framework adapter: [framework-streamlit.md](references/framework-streamlit.md), [framework-blazor.md](references/framework-blazor.md), or both only for a repository with both frontends.

## Establish product and repository truth

1. Read applicable `AGENTS.md` files and repository instructions.
2. Inspect product documentation, routes, entrypoints, components, layouts, shared styles, tokens, assets, public UI state, tests, screenshots, and realistic content shapes.
3. Identify the audience, primary job, critical workflow, supported platforms, framework, incumbent design system, and repository-discovered commands.
4. Read existing product or design context files when present. Never create `PRODUCT.md`, `DESIGN.md`, or an equivalent persistent context file unless the user explicitly requests one.
5. Preserve unrelated uncommitted work. Check Git state before editing and do not overwrite overlapping user changes.
6. Prefer the existing design system, native framework components, tokens, icon family, and typography. Do not add or replace a UI library, icon family, font dependency, or styling system without evidence and user authorization.

Use real copy and data shapes where available. Do not fabricate product capabilities, data, navigation, or states to make a screen appear complete.

## Classify the operation

Select one operation from the user's request:

- `audit`: inspect and report; do not edit.
- `refine`: improve hierarchy, clarity, consistency, accessibility, and responsive behavior while preserving recognizable identity and product behavior. Use this for vague requests such as "make it prettier," "clean up the UI," or "improve the interface."
- `polish`: make a narrow finishing pass within the established design language.
- `redesign`: replace the visual language only when the user explicitly asks for a redesign. Preserve product truth and functionality unless the request says otherwise.
- `create`: build a new product surface within repository, product, and framework conventions.

Skill activation does not expand mutation authority. An audit stays read-only, and a focused request stays within its stated scope.

Before implementation, state a concise Design Read containing:

- audience and primary job;
- desired qualities and appropriate information density;
- motion level;
- incumbent design system and constraints;
- selected operation and preservation boundaries.

## Preserve behavior deliberately

For refinement and polish, preserve routes, information architecture, terminology, semantics, parameters, state, analytics and test hooks, keyboard behavior, validation, error handling, and recognizable identity unless a specific change is authorized. For create and redesign work, identify equivalent preservation constraints before editing.

Trace each changed interaction through its handler, state transitions, loading and failure paths, and tests. Do not trade correctness, performance, or testability for visual novelty.

## Apply contextual product-UI judgment

Keep the actual page title as the semantic H1. Evaluate page introductions for information gain:

- Flag, but do not mechanically ban, eyebrows, kickers, overlines, generic subtitles, repeated card stacks, excessive pills, nested cards, purposeless gradients or glass effects, mixed icon styles, arbitrary tokens, competing primary actions, placeholder-only labels, hover-only behavior, fabricated data, and unbounded motion.
- Preserve genuine breadcrumb, status, audience, dateline, document-type, and step context using the semantic component appropriate to that information.
- Keep supporting text only when it adds scope, source, state, consequence, prerequisite, limitation, or next-step information.

Review all applicable loading, empty, zero-result, error, success, permission-denied, stale or offline, long-content, localized-content, large-dataset, destructive-action, light and dark, keyboard, zoom, and reduced-motion states. Treat WCAG 2.2 Level AA as a review baseline, not a claim of formal conformance.

## Route framework work

### Streamlit

Detect Streamlit from manifests, imports, configuration, or entrypoints. Read [framework-streamlit.md](references/framework-streamlit.md) and use the existing `$developing-with-streamlit` skill when it is available. Let that skill own version-matched framework mechanics while this skill owns product hierarchy, content, density, accessibility, states, consistency, and visual quality.

If version discovery or startup fails because Streamlit is absent, do not install it automatically. Continue from repository evidence and current official documentation when needed, run only safe available checks, and report rendered verification as blocked.

### Blazor

Detect Blazor from `.razor` components, `AddRazorComponents`, routing, and render-mode configuration. Read [framework-blazor.md](references/framework-blazor.md). Distinguish Blazor components from Razor Pages, which use `.cshtml` files and `PageModel`; never apply Razor Pages guidance merely because both use Razor syntax.

When a current ASP.NET Core skill is available, use it for framework correctness. Keep this skill responsible for design and rendered quality.

## Implement in a bounded pass

Make the smallest coherent set of changes that fulfills the selected operation. Reuse shared components and tokens when repetition is real, but do not create abstractions for a single cosmetic instance. Keep responsive and state behavior in the same change as the visual treatment that depends on it.

Use repository-discovered safe commands. Never invent commands, install missing runtimes, run deployments or migrations, access credentialed services, or invoke unrelated external systems without authorization.

## Verify the rendered result

When the application can be started safely, follow [visual-verification.md](references/visual-verification.md):

1. Capture one baseline pass before editing.
2. Apply one grouped implementation pass.
3. Perform one confirmation pass using screenshots, DOM state, interaction, console output, and source correlation.
4. Continue only for unresolved P0 or P1 problems.

Use repository-defined breakpoints. Otherwise inspect relevant widths from 375, 768, 1280, and 1920 pixels. Exercise keyboard navigation, visible and unobscured focus, 200% text zoom, reduced motion, long content, and the highest-risk available non-happy-path state.

If runtime or browser verification is unavailable, do not claim visual completion. State exactly what was source-tested and what remains unverified.

## Report findings and hand off

For audits, assign:

- `P0`: blocks use, accessibility, or a critical workflow.
- `P1`: materially harms comprehension, hierarchy, navigation, or task completion.
- `P2`: creates visible inconsistency, responsive weakness, or unfinished interaction quality.
- `P3`: optional expression, delight, or low-impact polish.

For each finding, include the route and state, screenshot or DOM evidence when available, source location, user consequence, proposed change, preservation constraint, and verification method.

For implementation, report the Design Read, selected operation, changes made, behavior preserved, routes, viewports and states inspected, commands and results, visual evidence, remaining risks, and explicit verification gaps.

Keep one primary design owner. If the host delegates work, restrict additional agents to non-overlapping inspection or verification, and have the primary agent validate and reconcile every conclusion.
