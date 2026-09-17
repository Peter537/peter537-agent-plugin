---
owner: Dispatch Product Council
status: maintained-context
scope: dispatch-console
---

# Dispatch design context

Operators compare route risk and assign shipments without losing evidence. The [product brief](../PRODUCT_BRIEF.md) and [ADR-031](../decisions/ADR-031-comparison-variants.md) approve compact desktop rows and larger tablet targets. Keep risk labels as text plus an icon and preserve the scoped amber evidence rail. British English is default; Danish is supported.

[`styles/tokens.css`](../styles/tokens.css) owns current token values. [`components/dispatch-contracts.md`](../components/dispatch-contracts.md) owns component and state contracts. This artifact references those sources rather than copying their implementation.

The new capture records have not been reconciled here. Exact breakpoints, motion, and final Danish state labels remain unresolved. This context does not approve itself or verify rendered or runtime behavior.
