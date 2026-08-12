# Browser-host safety and verification

Use this reference before creating, launching, inspecting, or removing a local browser host. Apply it to both maintained companions and temporary harnesses, with stricter release and data-isolation rules for the temporary lane.

## Temporary-harness eligibility

Use a temporary harness only when the requested evidence is narrow and short-lived, such as:

- route discovery and prerendered content;
- DOM hierarchy, CSS, responsive layout, and browser accessibility inspection;
- a deterministic component scenario that can run behind safe adapters;
- diagnosis of Web-host startup, static assets, or Blazor interactivity.

Prefer a maintained companion when browser development recurs, Web is a supported product target, authentication or multi-user behavior matters, or the harness would accumulate production logic.

Stop and propose a refactor when components directly depend on the MAUI executable, native lifecycle, or device APIs and no honest host-neutral adapter exists.

## Safe defaults

Configure a temporary harness with all of these defaults:

- bind only to loopback (`127.0.0.1`, `[::1]`, or an equivalent localhost configuration), never `0.0.0.0`, `+`, `*`, a LAN address, or a public tunnel;
- use deterministic, non-sensitive fixtures and a disposable writable data directory;
- display a persistent, unmistakable `DEVELOPMENT HARNESS` banner;
- disable or replace email, notifications, payments, uploads, device actions, destructive mutations, and external side effects;
- avoid loading developer secrets or the production application's credential store;
- keep the host outside production project references and release packaging;
- keep generated reference projects and disposable state out of source control;
- log only the minimum diagnostic data and never log tokens, credentials, sensitive fixture fields, or unnecessary personal paths.

An ignored directory is not enough on its own. Also inspect project references, solution membership, publish configuration, packaging inputs, CI globs, Docker contexts, and `git status` to prove the harness cannot enter a release accidentally.

## Real data and side effects

Do not expose real data or side-effecting services merely because the host is loopback-only. Obtain explicit authorization for the exact data and behavior, then define:

- purpose and minimum required records;
- read-only versus write behavior;
- authentication or per-session access control;
- anti-forgery and authorization requirements;
- least-privilege service adapters;
- data retention and cleanup;
- log redaction;
- rollback or recovery for mutations.

If those protections cannot be established, keep the harness on fixtures and mark the real-data scenario blocked.

## Launch and process control

Before launch:

1. Use the repository-pinned SDK when available.
2. Confirm the required SDK, workload, and template are already installed; do not install missing prerequisites automatically.
3. Resolve a free loopback port deliberately and avoid colliding with an existing process.
4. Record the exact project, configuration, environment variables, fixture root, and expected URL without exposing secrets.

After launch:

1. Identify the process started by the task and confirm its listener is loopback-only.
2. Wait for a positive readiness signal or probe a health/root route with a bounded timeout.
3. Preserve startup errors. Do not repeatedly restart a failing host without diagnosing the first failure.
4. Stop only processes created by the task during teardown.

## Browser verification ladder

Record every layer separately because later layers do not follow automatically from earlier ones.

### 1. Transport and route

Verify the expected status, content type, redirects, route, and required static assets. Check deep links rather than only the root page.

### 2. Prerendered DOM and presentation

Inspect semantic DOM, visible content, CSS application, viewport behavior, keyboard order, labels, and obvious browser accessibility signals. A screenshot is supporting evidence, not the sole source of truth.

### 3. Interactive runtime

Prove that the configured Blazor runtime or circuit starts. For Interactive Server, inspect browser console output and the expected `/_blazor` negotiation and SignalR transport. For WebAssembly or Auto, inspect resource loading and runtime startup appropriate to that mode.

Signs of unproven or failed interactivity include:

- no expected interactive transport or runtime activity;
- negotiation, WebSocket, long-polling, boot-resource, or JavaScript errors;
- buttons, forms, dialogs, or navigation that render but do not invoke handlers;
- DOM that never reflects a triggered state change;
- a server-rendered link that works only because it performs a full page load.

### 4. User workflow

Exercise deterministic scenarios that include event callbacks and observable state transitions. Cover validation, loading, empty, error, disabled, and confirmation states when relevant. Use separate sessions when state isolation matters.

### 5. Native host

Run a separate native lane for claims about:

- `BlazorWebView` or WebView2 integration;
- MAUI XAML shell/window behavior;
- device APIs, permissions, file pickers, secure storage, or sensors;
- application lifecycle, suspend/resume, deep links, and native navigation;
- native accessibility trees, keyboard/platform conventions, packaging, signing, installation, and release performance.

Browser success can guide shared UI development but cannot pass any of these native checks.

## Diagnostic matrix

| Observation | Supported conclusion | Unsupported conclusion |
| --- | --- | --- |
| Route returns expected HTML | Host and prerender path work | Blazor callbacks work |
| DOM and CSS match at target viewports | Browser presentation is supported | Native WebView presentation is identical |
| `/_blazor` connects and a counter/state change works | Interactive Server works for that scenario | All workflows and sessions are correct |
| Fixture-backed save changes isolated state | Harness adapter and fixture mutation work | Production storage is safe or correct |
| Native test passes in `BlazorWebView` | Tested native scenario works on that target | Other platforms or release packages work |

Use `VERIFIED`, `FAILED`, `NOT_TESTED`, or `BLOCKED` for each evidence layer. Never replace missing evidence with `PASS`.

## Teardown checklist

- Stop the exact host and helper processes started by the task.
- Confirm the loopback listener has closed.
- Remove disposable data and generated reference solutions when they are no longer needed and deletion is safe.
- Retain tracked implementation changes only when the user requested them.
- Confirm temporary paths are absent from publish, package, container, and CI inputs.
- Recheck `git status` and report any intentionally retained development-only files.
- Record evidence limits, especially when prerendering worked but interactivity or native verification did not.
