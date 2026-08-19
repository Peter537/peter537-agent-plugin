---
name: maui-blazor-browser
description: Prepare, assess, implement, and verify safe browser-development paths for .NET MAUI Blazor Hybrid UI by reusing or creating a companion Blazor Web host, or by creating an isolated temporary browser harness around host-neutral Razor Class Library UI. Use when a MAUI Blazor Hybrid project needs browser inspection, browser-driven development, responsive or DOM verification, shared MAUI-and-Web UI, host-specific service adapters, or diagnosis of a browser host that prerenders but does not become interactive. Do not use for ordinary Blazor Web applications, native-only MAUI/XAML work, visual-polish-only requests, or browser testing unrelated to MAUI Blazor Hybrid.
license: MIT
---

# MAUI Blazor Browser

Make shared MAUI Blazor Hybrid UI safely accessible to a browser without turning the native application into a server or overstating what browser evidence proves.

## Non-negotiable boundaries

- Preserve repository instructions, user scope, and existing architecture. Treat review or diagnosis requests as read-only unless implementation is authorized.
- Keep the native MAUI executable free of silently introduced listeners, server endpoints, server render modes, and browser-only dependencies.
- Never make a Web host reference the MAUI executable. Move shareable Razor UI and abstractions into a host-neutral RCL instead.
- Never expose production data, secrets, privileged operations, or non-loopback listeners through a temporary harness by default.
- Never install workloads, templates, packages, browsers, or tools without authorization. Use `$audit-dependencies` before adding or changing any package, tool, or workload.
- Never equate a rendered page or screenshot with a working interactive Blazor circuit, and never equate browser behavior with native behavior.

## Read the focused references

- Read [dual-host-architecture.md](references/dual-host-architecture.md) before selecting or changing the project topology, render modes, DI boundaries, static assets, or host-specific adapters.
- Read [browser-host-safety-and-verification.md](references/browser-host-safety-and-verification.md) before creating or running a local browser host and before reporting browser or native evidence.

## Workflow

### 1. Establish repository state

1. Read repository instruction files that govern the root and every directory in scope.
2. Record Git status and preserve unrelated or pre-existing changes.
3. Inspect `global.json`, target frameworks, installed SDK information, workloads already present, solution and project files, project references, package sources, and central package management.
4. Map MAUI hosts, Razor Class Libraries, existing Web hosts, Razor routes, layouts, render-mode declarations, static assets, service registration, native API usage, tests, launch profiles, and browser-test infrastructure.
5. Identify stateful or side-effecting services, data roots, credentials, network clients, device services, platform conditionals, and components that reference MAUI types directly.

Do not generate a reference solution until the repository's pinned or active SDK is known. When scaffolding is useful and the required template is already available, generate it in a disposable temporary directory and inspect its current structure rather than copying a bundled template.

### 2. Select one lane

Choose the smallest safe lane that satisfies the request:

| Situation | Lane |
| --- | --- |
| A safe browser host already exposes the relevant host-neutral UI | Reuse and verify the existing host. |
| Browser development will recur or Web is a real supported target | Maintain a tracked Blazor Web companion sharing an RCL. |
| The task is one-off route, DOM, CSS, or responsive inspection | Use an ignored, release-excluded temporary harness with isolated fixtures. |
| Razor UI directly depends on MAUI, platform, or native executable types | Stop browser-host work and propose the smallest host-neutral refactor first. |
| The repository prohibits a Web host or the required runtime is unavailable | Report the constraint and do not claim rendered verification. |

Prefer Interactive Server for a companion to an existing Hybrid application unless repository requirements establish WebAssembly or Auto. Preserve an existing deliberate render-mode choice rather than replacing it reflexively.

### 3. Establish host-neutral boundaries

1. Keep shared Razor components, layouts, CSS, static assets, contracts, and browser-safe presentation logic in an RCL that does not reference MAUI.
2. Keep MAUI implementations and native capabilities in the MAUI host; keep Web implementations and Web-only infrastructure in the Web host.
3. Register host-specific implementations behind shared interfaces. Preserve per-user isolation in Web DI; do not translate MAUI singleton state into a Web singleton when the state belongs to one user or circuit.
4. Resolve routes, static assets, render modes, antiforgery, and interactive services using the active SDK's generated reference structure and official documentation.
5. If the repository needs new packages or workloads, pause this workflow and invoke `$audit-dependencies` before any installation or manifest change.

### 4. Harden temporary harnesses

For a temporary lane, use deterministic non-sensitive fixtures, a disposable writable data root, loopback-only binding, explicit development configuration, and an unmistakable browser banner. Keep the harness outside production project references, packaging, publishing, and release artifacts. Confirm its files are ignored or otherwise intentionally untracked and confirm Git status after use.

Require explicit authorization before using real data or side-effecting services. Then add protections proportionate to the data and behavior, such as session authentication, least-privilege adapters, read-only operation, anti-forgery controls, and narrowly scoped endpoints. Never log secrets, access tokens, sensitive records, or unnecessary absolute paths.

### 5. Run the host without hiding failures

Use existing repository commands and already-installed runtimes. Capture the exact launch command, environment, URL, binding, data source, and process identity. Prefer an ephemeral or deliberately selected free loopback port. Confirm the listener before opening a browser.

Prefer the signed-in in-app Browser for a safe local Web app when it is available. Otherwise use the repository's existing browser-testing route. If neither exists, prepare or assess the host but mark rendered verification as blocked.

### 6. Verify evidence in layers

Verify and report each layer independently:

1. **Host availability:** process starts, loopback listener responds, expected route and assets load.
2. **Prerendered output:** route content, DOM, styles, layout, and responsive behavior are present before interactivity is proven.
3. **Blazor interactivity:** the interactive circuit or runtime starts without console or transport failure; callbacks, forms, dialogs, navigation, and state transitions actually execute.
4. **Browser workflow:** deterministic user scenarios succeed and state changes are isolated and observable.
5. **Native workflow:** separate native tests verify `BlazorWebView`, WebView2, XAML, device APIs, lifecycle, packaging, native accessibility, and release behavior where relevant.

Treat missing `/_blazor` traffic, failed negotiation, console exceptions, unresponsive controls, or absent state changes as failed or unproven interactivity even when the DOM looks correct. Preserve screenshots, DOM observations, logs, requests, and test output only to the extent needed and privacy-safe.

### 7. Teardown and report

Stop processes that this task started, remove disposable data and temporary generated references when safe, and verify that no listener or release artifact remains. Do not delete pre-existing user files or processes.

Report:

- selected lane and why it fits;
- project and service boundaries changed or proposed;
- host command, binding, fixture source, and isolation controls;
- route-rendering, interactivity, browser-workflow, and native evidence as separate results;
- blocked or unverified areas without converting them into passes;
- cleanup performed and any remaining development-only files;
- follow-up work, including `$ui-design-and-polish` when visual design itself should change.

Use precise labels such as `VERIFIED`, `FAILED`, `NOT_TESTED`, and `BLOCKED` per evidence layer.
