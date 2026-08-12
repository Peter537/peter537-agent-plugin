# Dual-host architecture

Use this reference to design or assess the maintained Blazor Web companion and its shared RCL boundary. Prefer the active SDK's generated structure and current official Microsoft documentation over memorized project scaffolding.

Primary reference: [Build a .NET MAUI Blazor Hybrid app with a Blazor Web App](https://learn.microsoft.com/en-us/aspnet/core/blazor/hybrid/tutorials/maui-blazor-web-app?view=aspnetcore-10.0).

## Target topology

Use three conceptual layers when both native and Web targets are maintained:

```text
Host-neutral Razor Class Library
  - Razor components, routes, layouts, CSS, static assets
  - contracts and browser-safe presentation logic
  - no reference to the MAUI executable or platform APIs

MAUI Blazor Hybrid host
  - BlazorWebView and native application lifecycle
  - platform/device integrations
  - MAUI implementations of shared contracts

Blazor Web host
  - ASP.NET Core startup, endpoints, and render modes
  - Web implementations of shared contracts
  - per-user or per-circuit state isolation
```

Project names and file locations can differ. Evaluate boundaries through project references and type usage, not folder names alone.

## Inspect before changing

Inventory:

- solution files, project SDKs, target frameworks, project references, and conditional items;
- `global.json`, installed SDKs, installed workloads, and any repository bootstrap commands;
- routable components, layouts, imports, shared assemblies, and root components;
- `AddMauiBlazorWebView`, `AddRazorComponents`, interactive component services, and endpoint mappings;
- `@rendermode`, root render-mode configuration, and whether interactivity is global or per-page;
- `wwwroot`, scoped CSS, `_content/{library}/...` assets, fonts, scripts, and service workers;
- DI registrations, service lifetimes, persistent state, authentication, authorization, and antiforgery;
- direct uses of `Microsoft.Maui`, platform namespaces, `BlazorWebView`, device APIs, file pickers, secure storage, sensors, or native windows inside shared UI.

## Generate reference structure safely

When the repository's active SDK includes the official combined MAUI Blazor Hybrid and Web template, inspect its current help and generate a disposable reference solution. A typical template identity is `maui-blazor-web`, with an interactivity option selected for the Web host. Do not assume an old command line still matches the installed SDK; query the installed template first.

Use the generated solution only as evidence for current project references, root components, render-mode setup, static assets, and service registration. Do not copy it wholesale into a mature repository. Do not install a missing workload or template without authorization, and do not let a generated reference modify the repository.

## Choose the Web render mode

Prefer Interactive Server when adding browser development to an existing Hybrid application because it usually minimizes client-side constraints and keeps .NET execution on the server. Choose Interactive WebAssembly or Auto only when the repository has a real client-side deployment requirement and its dependencies can run safely in the browser.

MAUI Blazor Hybrid UI is interactive inside `BlazorWebView`, while a Blazor Web host has explicit render modes. Make the Web host's intended interactivity unambiguous. Global interactivity is often the closest browser companion for shared Hybrid UI; configure the Web host's root `Routes` and `HeadOutlet`, interactive services, endpoint render mode, and `blazor.web.js` consistently. Keep Web render-mode declarations out of shared RCL pages when those pages also run in MAUI. With per-page or per-component interactivity, verify each routable component and do not apply conflicting render modes.

Prerendering can produce valid HTML before the interactive runtime starts. Therefore render mode selection is incomplete until an actual event callback and state transition pass.

## Keep the RCL host-neutral

Good shared candidates include:

- Razor pages/components, layouts, navigation models, validation, and view models;
- CSS, scoped CSS, icons, localization resources, and other static assets;
- interfaces for files, dialogs, notifications, clipboard, environment details, storage, and domain services;
- pure application logic that has no platform or server dependency.

Keep these out of the RCL unless guarded behind a host-neutral contract:

- `MauiApp`, `Application`, `Window`, `Page`, handlers, and `BlazorWebView`;
- platform-specific namespaces or compile targets;
- device, filesystem, secure-storage, sensor, windowing, or native-dialog implementations;
- ASP.NET Core host startup, server endpoints, cookies, or server-only authentication implementation.

If a Razor component imports a native namespace, inject a shared interface instead. Implement it separately in MAUI and Web. A Web substitute may be fully functional, deliberately read-only, a deterministic fixture, or an explicit unsupported-operation adapter; it must not silently pretend that native behavior occurred.

## Preserve correct service lifetimes

Reason about ownership rather than copying registrations:

- MAUI applications often use singleton services for application-wide state.
- Blazor Web user state normally needs scoped or circuit-aware services so one user's state cannot leak into another user's session.
- Truly stateless services can often remain transient or singleton, subject to thread safety.
- A temporary single-user harness still should not normalize unsafe singleton design for a maintained Web target.

Document intentional lifetime differences between hosts. Test simultaneous or isolated sessions when the Web target can serve more than one user.

## Static assets and routes

Confirm the Web host serves RCL assets using the framework's generated static-web-asset mapping rather than copied, divergent files. Verify scoped CSS bundles, content paths, fonts, scripts, and images in both hosts. Do not patch around a missing asset with machine-specific absolute paths.

Keep route discovery aligned with the assemblies containing routable components. For an RCL, verify both router assembly discovery and endpoint additional-assembly configuration using the APIs emitted by the active SDK's template. Verify the default route, deep links, navigation fallbacks, not-found behavior, and any authorization boundaries. A route that exists only in prerendered HTML is not yet an interactive success.

## Existing companion hosts

Reuse an existing maintained Web companion when it:

- references the host-neutral RCL rather than the MAUI executable;
- has deliberate render-mode and DI configuration;
- has safe data sources and an understood launch path;
- is included or excluded from release artifacts intentionally;
- can exercise the requested routes without weakening security.

Repair a concrete defect in that host instead of adding a second competing host.
