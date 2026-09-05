---
owner: Fulfilment Product Council
status: approved
scope: dispatch-console
last_reviewed: 2026-08-29
---

# Dispatch console design context

## Product and workflow

Dispatch operators compare ordered route risk and assign a shipment without leaving the queue. Preserve route order, assignment permission and confirmation, and text-plus-icon risk labels. Support permission-denied, stale-route, empty, loading, and assignment-error states.

These are approved decisions from the [product brief](../PRODUCT_BRIEF.md) and [ADR-011](../decisions/ADR-011-dispatch-variants.md). Current ordering and assignment behavior are observed in the [implementation](../app/dispatch.py) and [tests](../tests/test_dispatch.py); those sources do not create additional product approval.

## Locale and platform

British English is the default locale, and Danish is supported. Web uses compact comparison rows. Tablet uses larger touch targets and one expanded route at a time. Exact breakpoints, final localized copy, and transition details remain unresolved.

## Scoped visual identity

The narrow amber rail may anchor risk evidence only in the route comparison column. Its purpose is to preserve the risk-evidence relationship while operators scan; it is not a global brand colour.

The ownerless [redesign note](../notes/old-redesign.md) is exploratory and does not govern. Do not replace the queue with marketing cards, reduce risk to colour or icons alone, or introduce its proposed component library.

## Canonical systems

[`styles/tokens.css`](../styles/tokens.css) owns current values for `--surface-panel`, `--text-primary`, `--status-risk-border`, `--space-control-inline`, `--focus-ring`, and `--target-tablet-min`; values are intentionally not duplicated here.

[`components/dispatch-contracts.md`](../components/dispatch-contracts.md) is canonical for `RouteRiskStatus`, `AssignmentAction`, and their state and test-hook contracts. CSS values and DOM nesting are implementation details.

## Exemplar boundary

`EXP-011` may inform stable evidence grouping for desktop dispatch comparison only. It comes from the Internal operations pattern collection, is approved for internal reference, has no tablet evidence, and reflects a different product identity. Use only the grouping principle; do not copy layout, palette, content, assets, or code. See the canonical [exemplar record](../design/exemplars.json).

## Open evidence limits

Product-specific motion, exact responsive dimensions, final state recovery, announcements, focus behavior, and design-system rules beyond the named sources remain unresolved. This context does not prove rendered, runtime, accessibility, or acceptance behavior.
