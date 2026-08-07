# Visual Verification

Rendered verification is required whenever the application can be started safely. Use browser evidence to validate hierarchy, responsive behavior, interaction, state, and accessibility; source inspection alone cannot confirm visual completion.

## Establish a safe launch path

1. Read repository instructions, manifests, development configuration, and test setup.
2. Use an existing non-deploying development or test command. Do not invent commands, install dependencies, run migrations, or connect to credentialed or production services without authorization.
3. Check whether the command writes data, sends messages, launches external systems, or requires secrets before running it.
4. Record the URL, route, test account or fixture state, command, process state, and any limitations.

If no safe runnable path exists, continue with source and configured test evidence, then state the exact visual-verification gap.

## Baseline pass

Capture the current surface before editing:

- the primary route and critical workflow;
- relevant repository-defined breakpoints, or applicable widths from 375, 768, 1280, and 1920 pixels;
- the default state and highest-risk available non-happy-path state;
- screenshots plus DOM or accessibility-tree state where available;
- console errors and warnings;
- keyboard order, focus visibility, overlays, scrolling, and sticky elements;
- long content, realistic dense data, and current theme variants when supported.

Map visible defects to source files and components before changing code. Do not infer a source location from appearance alone when DOM, source maps, or repository search can confirm it.

## Grouped implementation pass

Implement one coherent batch based on the baseline. Keep behavioral and state safeguards next to the visual changes that depend on them. Run repository-discovered targeted tests, type checks, builds, or component tests before browser confirmation.

## Confirmation pass

Repeat the relevant baseline evidence after editing and compare:

- visual hierarchy and alignment;
- wrapping, clipping, overflow, and reflow;
- visible and unobscured keyboard focus;
- pointer, touch, and keyboard operation;
- 200% text zoom;
- reduced-motion behavior;
- loading, empty, error, permission, or destructive state selected as highest risk;
- console output and failed network requests;
- route, filter, form, selection, and back-navigation state;
- test and automation hooks that the change could affect.

Use screenshots as evidence, not as the only test. Inspect the DOM, accessible name and role, computed state, interaction result, console, and source correlation when those tools are available.

## Bound iteration

Use one baseline pass, one grouped implementation pass, and one confirmation pass. Continue only to correct unresolved:

- `P0` issues that block use, accessibility, or a critical workflow;
- `P1` issues that materially harm comprehension, navigation, or task completion.

Report remaining P2 and P3 observations rather than entering an open-ended cosmetic loop.

## Evidence and handoff

Record:

- routes, states, themes, and viewports inspected;
- before and after screenshot locations or captured browser evidence;
- interactions and accessibility checks performed;
- commands and results;
- console or network issues;
- source files correlated to the rendered changes;
- any blocked route, state, viewport, runtime, browser, or assistive-technology check.

Do not say "pixel perfect," "fully responsive," "accessible," or "visually complete" when the available evidence does not support that scope.
