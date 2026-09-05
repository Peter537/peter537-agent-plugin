---
name: ui-design-and-polish
description: Design, audit, refine, redesign, create, and polish task-oriented product interfaces using repository evidence and rendered verification, including requests to correct generic, templated, homogenized, or insufficiently product-specific UI. Also use for direct requests to create or maintain persistent project design context from repository evidence and explicit human decisions. Use for dashboards, data tools, forms, settings, workflows, application shells, page hierarchy, UI copy when hierarchy or interaction context is in scope, responsive behavior, accessibility, interaction states, design-system consistency, Streamlit interfaces, and Blazor Web Apps. Do not use for backend-only work, ordinary non-UI framework tasks, comprehensive documentation maintenance, other documentation-only changes, image-only work, wording-only UI copy, or marketing, editorial, and commerce surfaces.
license: MIT
---

# UI Design and Polish

Improve product interfaces without losing product truth, framework behavior, or accessibility. Base decisions on repository evidence and the rendered application, not generic visual trends.

## Load guidance by operation and concern

Read only the references that change the current task:

| Condition | Read |
| --- | --- |
| The task audits or materially changes product layout, density, navigation, actions, responsive composition, tokens, or components, or creates or redesigns a surface | [product-ui.md](references/product-ui.md) |
| The task changes headings, introductions, labels, helper text, buttons, messages, or empty states | [content-and-hierarchy.md](references/content-and-hierarchy.md) |
| The task can affect semantics, controls, focus, contrast, zoom or reflow, motion, forms, or application states | [accessibility-and-states.md](references/accessibility-and-states.md) |
| The task creates or redesigns a surface, makes a consequential visual-language change, explicitly raises generic, templated, homogenized, or product-specificity concerns, or discovers a material specificity candidate during review | [visual-direction-and-specificity.md](references/visual-direction-and-specificity.md) |
| A rendered application can be inspected safely | [visual-verification.md](references/visual-verification.md) |
| The affected frontend is Streamlit or Blazor | Read exactly the detected adapter: [framework-streamlit.md](references/framework-streamlit.md), [framework-blazor.md](references/framework-blazor.md), or both only when both frontends are in scope |

For a narrow audit or polish request, do not load unrelated framework, content, or visual-direction guidance merely because it exists.

## Establish product and repository truth

1. Read applicable `AGENTS.md` files and repository instructions.
2. Inspect product documentation, routes, entrypoints, components, layouts, shared styles, tokens, assets, public UI state, tests, screenshots, and realistic content shapes relevant to the requested surface.
3. Identify the audience, primary job, critical workflow, supported platforms, framework, incumbent design system, and repository-discovered commands.
4. Read existing product or design context files when present. Never create `PRODUCT.md`, `DESIGN.md`, or an equivalent persistent context file unless the user explicitly requests one.
5. Preserve unrelated uncommitted work. Check Git state before editing and do not overwrite overlapping user changes.
6. Prefer the existing design system, native framework components, tokens, icon family, and typography. Do not add or replace a UI library, icon family, font dependency, or styling system without evidence and user authorization.

Use real copy and data shapes where available. Do not fabricate product capabilities, data, navigation, or states to make a screen appear complete.

## Classify the operation

Select one operation from the user's request:

- `audit`: inspect and report; do not edit.
- `refine`: improve hierarchy, clarity, consistency, accessibility, specificity, and responsive behavior while preserving recognizable identity and product behavior. Use this for vague requests such as "make it prettier," "clean up the UI," or "improve the interface."
- `polish`: make a narrow finishing pass within the established design language.
- `redesign`: replace the visual language only when the user explicitly asks for a redesign. Preserve product truth and functionality unless the request says otherwise.
- `create`: build a new product surface within repository, product, and framework conventions.

Skill activation does not expand mutation authority. An audit stays read-only, and a focused request stays within its stated scope.

Before implementation, or before reaching design conclusions in an audit, state a concise Design Read containing:

- audience and primary job;
- desired qualities and appropriate information density;
- motion level;
- incumbent design system and constraints;
- selected operation and preservation boundaries.

When [visual-direction-and-specificity.md](references/visual-direction-and-specificity.md) applies, add a Visual Direction Contract covering the user job, product evidence, incumbent system, differentiating choices, familiar conventions to retain, and patterns that would be inappropriate for this product. Do not invent a distinctive style where repository and product evidence support a deliberately neutral interface.

## Preserve behavior deliberately

For refinement and polish, preserve routes, information architecture, terminology, semantics, parameters, state, analytics and test hooks, keyboard behavior, validation, error handling, and recognizable identity unless a specific change is authorized. For create and redesign work, identify equivalent preservation constraints before editing.

Trace each changed interaction through its handler, state transitions, loading and failure paths, and tests. Do not trade correctness, performance, or testability for visual novelty.

## Apply contextual product-UI judgment

Keep the actual page title as the semantic H1. Evaluate page introductions for information gain:

- Treat eyebrows, kickers, overlines, generic subtitles, repeated card stacks, excessive pills, nested cards, purposeless gradients or glass effects, mixed icon styles, arbitrary tokens, competing primary actions, placeholder-only labels, hover-only behavior, fabricated data, and unbounded motion as contextual signals, never automatic defects.
- Preserve genuine breadcrumb, status, audience, dateline, document-type, and step context using the semantic component appropriate to that information.
- Keep supporting text only when it adds scope, source, state, consequence, prerequisite, limitation, or next-step information.
- For a specificity concern, use `confirmed`, `probable`, `candidate`, or `exempted` according to product evidence, rendered evidence, repository evidence, and the heuristic's limits. Never infer genericity from a component type alone.

Review the application states relevant to the changed surface, including its highest-risk non-happy path. Consider loading, empty, zero-result, error, success, permission-denied, stale or offline, long-content, localized-content, large-dataset, destructive-action, light and dark, keyboard, zoom, and reduced-motion states according to actual product behavior. Treat WCAG 2.2 Level AA as a review baseline, not a claim of formal conformance.

## Route framework work

### Streamlit

Detect Streamlit from manifests, imports, configuration, or entrypoints. Read [framework-streamlit.md](references/framework-streamlit.md) and use the existing `$developing-with-streamlit` skill when it is available. Let that skill own version-matched framework mechanics while this skill owns product hierarchy, content, density, accessibility, states, consistency, and visual quality.

If version discovery or startup fails because Streamlit is absent, do not install it automatically. Continue from repository evidence and current official documentation when needed, run only safe available checks, and report rendered verification as blocked.

### Blazor

Detect Blazor from `.razor` components, `AddRazorComponents`, routing, and render-mode configuration. Read [framework-blazor.md](references/framework-blazor.md). Distinguish Blazor components from Razor Pages, which use `.cshtml` files and `PageModel`; never apply Razor Pages guidance merely because both use Razor syntax.

When a current ASP.NET Core skill is available, use it for framework correctness. Keep this skill responsible for design and rendered quality.

## Implement and verify in a bounded pass

Make the smallest coherent set of changes that fulfills the selected operation. Reuse shared components and tokens when repetition is real, but do not create abstractions for a single cosmetic instance. Keep responsive and state behavior in the same change as the visual treatment that depends on it.

Use repository-discovered safe commands. Never invent commands, install missing runtimes, run deployments or migrations, access credentialed services, or invoke unrelated external systems without authorization.

When the application can be started safely, follow [visual-verification.md](references/visual-verification.md): capture a baseline, apply one coherent implementation batch, then repeat the relevant rendered and behavioral evidence. Use repository-defined breakpoints; otherwise select applicable widths from 375, 768, 1280, and 1920 pixels. Exercise keyboard navigation, visible and unobscured focus, 200% text zoom, reduced motion, long content, and the highest-risk available non-happy-path state when relevant.

Bound further iteration by the operation:

- For `refine`, resolve relevant in-scope P0-P2 issues; report unrelated or optional P3 observations.
- For `polish`, resolve the requested finishing issues, including relevant P2-P3 details, and any P0-P1 regression introduced by the work; do not expand into an open-ended redesign.
- For `create` and `redesign`, resolve in-scope P0-P2 issues required by the direction contract, preservation boundaries, and affected states; pursue P3 expression only when the request or established system requires it.
- For `audit`, do not enter an implementation loop.

If runtime or browser verification is unavailable, do not claim visual completion. State exactly what was source-tested and what remains unverified.

## Close and report

Classify audit findings by user consequence:

- `P0`: blocks use, accessibility, or a critical workflow.
- `P1`: materially harms comprehension, hierarchy, navigation, or task completion.
- `P2`: creates visible inconsistency, responsive weakness, product-generic treatment, or unfinished interaction quality.
- `P3`: optional expression, delight, or low-impact polish.

For each finding, include the route and state, screenshot or DOM evidence when available, source location, user consequence, proposed change, preservation constraint, and verification method. For specificity findings, also include the status and evidence layers described in [visual-direction-and-specificity.md](references/visual-direction-and-specificity.md).

Return one task-completion outcome:

- `PASS`: the requested audit is complete even if it reports findings; or the requested implementation meets its operation-specific completion conditions with no known in-scope regression.
- `FAIL`: available evidence shows that a required in-scope condition remains unmet or that the change introduced a regression.
- `BLOCKED`: necessary repository, runtime, rendered, authorization, or state evidence cannot be obtained safely enough to determine completion.

The outcome assesses completion of the authorized task, not an interface's universal quality and not a numerical score. For implementation, report the Design Read, material changes, behavior preserved, routes, viewports and states inspected, commands and results, visual evidence, remaining risks, and explicit verification gaps. Do not expose internal routing details unless they clarify a material limitation or trade-off.

Keep one primary design owner. If the host delegates work, restrict additional agents to non-overlapping inspection or verification, and have the primary agent validate and reconcile every conclusion.
