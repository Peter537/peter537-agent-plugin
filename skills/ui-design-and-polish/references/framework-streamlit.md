# Streamlit Adapter

Use this thin adapter to translate product-UI decisions into native Streamlit mechanisms. Let the available `$developing-with-streamlit` skill provide version-matched API and implementation guidance; do not duplicate or override it here.

## Detect and establish the version

Treat manifests, lockfiles, `.streamlit` configuration, `import streamlit`, and application entrypoints as evidence. Run the version-discovery workflow from `$developing-with-streamlit` when available.

If the configured environment lacks Streamlit:

- do not install or upgrade it automatically;
- use declared version constraints, lockfiles, repository code, and current official documentation when research is necessary;
- run only available static or unit checks;
- report application startup and real-browser verification as blocked.

## Prefer native composition

- Use native page configuration, navigation, containers, columns, tabs, dialogs, forms, status, and theme mechanisms supported by the detected version.
- Keep one clear page title and an ordered heading structure.
- Use native widgets with visible labels and help text before custom HTML controls.
- Keep wide layouts intentional and verify data-heavy surfaces at narrow widths rather than assuming column collapse is sufficient.
- Prefer the configured theme and stable CSS hooks. Scope custom CSS narrowly and avoid selectors tied to generated DOM internals.
- Use custom components only when native controls cannot meet a demonstrated product need.

## Preserve rerun and state behavior

- Treat every interaction as a possible rerun. Preserve widget values, filters, navigation, query parameters, and expensive results intentionally.
- Keep widget keys stable and unique; do not change them in a visual refactor without tracing state and tests.
- Do not mutate widget-backed session state in unsupported order.
- Use forms when grouped submission is the intended workflow, and keep validation and pending feedback clear.
- Keep query state and shareable URLs intact where the product relies on them.
- Verify cache boundaries and fragments when UI changes alter what reruns or refreshes.

## Accessibility and content

- Provide meaningful widget labels even when the visual design minimizes chrome. If a supported label-visibility option is used, confirm the accessible name remains present.
- Do not rely on Markdown or unsafe HTML to simulate controls.
- Ensure custom CSS does not remove focus indicators, hide required labels from assistive technology, reduce target usability, or break light and dark themes.
- Distinguish loading, empty, zero-result, error, stale, and success states with native status patterns where suitable.

## Test and verify

- Preserve and extend existing `AppTest` coverage for widget state, reruns, navigation, messages, and failure paths.
- Treat `AppTest` as behavioral evidence, not a substitute for a real browser.
- When runnable, verify screenshots, DOM, keyboard focus, responsive behavior, themes, long data, and the highest-risk state in a real browser.
- Record the discovered Streamlit version, startup command, tests run, and any version or runtime gap.
