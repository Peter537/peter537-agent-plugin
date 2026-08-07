# Blazor Adapter

Use this adapter for Blazor Web Apps and Blazor components. Use an available current ASP.NET Core skill for framework and platform correctness; keep this skill focused on product UI, content, accessibility, state, and rendered verification.

## Detect the application model

Confirm Blazor through evidence such as:

- `.razor` components with `@page` routes;
- `AddRazorComponents` and mapped Razor Components;
- interactive server, WebAssembly, auto, or static server rendering configuration;
- component layouts, `Routes`, `Router`, and render-mode directives.

Do not confuse Blazor with Razor Pages. Razor Pages primarily use `.cshtml` files plus `PageModel`; the shared Razor syntax does not make their lifecycle, routing, or interaction model equivalent.

## Preserve component contracts

- Keep route templates, component parameters, cascading parameters, query binding, navigation, and authorization behavior intact unless the task changes them.
- Trace event handlers, `@bind` behavior, validation, asynchronous operations, cancellation, and disposal before rearranging controls.
- Preserve stable test selectors and analytics hooks.
- Do not move code across render-mode boundaries without accounting for serialization, interactivity, prerendering, and state restoration.
- Avoid unnecessary JavaScript interop; use it only for browser capabilities or libraries that Blazor cannot provide cleanly.

## Structure the page

- Use `PageTitle` for the browser title and one semantic H1 for the page itself.
- Keep layouts responsible for shared shell, navigation, landmarks, and recurring chrome.
- Extract shared components when a repeated interaction or visual contract exists, not merely to shorten a file.
- Use component-scoped CSS for local styles and established global tokens or utilities for shared rules.
- Preserve CSS isolation expectations, specificity, theme behavior, and load order.

## Forms, state, and feedback

- Preserve the `EditForm` model, validation context, field identifiers, validation messages, and submit semantics.
- Keep labels associated with controls and surface validation in a useful order.
- Prevent duplicate actions during asynchronous work and expose progress, success, and recovery.
- Distinguish component-local state from scoped services, persisted state, query state, and server state.
- Account for prerendering and reconnect behavior when the selected render mode makes them relevant.
- Keep authorization-aware UI consistent with server-side enforcement; hidden controls are not an authorization boundary.

## Accessibility and interaction

- Prefer semantic HTML and established components over clickable generic elements.
- Preserve keyboard operation, focus management, accessible names, live status, dialog behavior, and logical DOM order.
- Do not let conditional rendering strand focus or remove the only recovery action.
- Verify responsive navigation, validation summaries, tables, dialogs, and loading transitions in the browser.

## Test and verify

- Discover and run existing component, integration, and browser tests that cover the changed surface.
- Test parameter and binding behavior, handlers, validation, authorization-visible states, navigation, render mode, and non-happy paths.
- When runnable, use browser evidence for screenshots, DOM, accessible state, keyboard interaction, console errors, reconnection or loading states, and relevant viewports.
- Record the detected application model and render mode. If runtime or browser verification is unavailable, identify the source and test evidence used and the exact remaining gap.
