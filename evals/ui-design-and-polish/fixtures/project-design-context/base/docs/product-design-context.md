---
owner: Cold-chain product design and operations
status: approved
approved: 2026-08-20
applies_to: exception-review
---

# Exception-review design context

This is the current product-direction source for the exception-review surface. It records approved product decisions, not permission to change dependencies, shared systems, or other repository files.

## Authority and scope

- Explicit task requirements and preserved behavior remain authoritative.
- This document owns product direction for the exception-review surface.
- `styles/tokens.css` owns semantic token names and values.
- `styles/components.css` owns shared status and action component contracts.
- `app.js` and the repository tests own the currently supported state transitions, keyboard behavior, and stable test hooks.
- Accessibility requirements cannot be waived by visual direction.
- Material with no current owner or approval status is exploratory evidence, not an accepted decision.

## User and job

Cold-chain coordinators compare live shipment exceptions and decide whether a load can continue, needs review, or must be quarantined. They work repeatedly and under time pressure. The shared sensor source and freshness apply to the complete visible list; keep that provenance adjacent to the list, and keep each record's age, temperature, threshold, and facility easy to compare without opening it. Per-shipment source values are not available and must not be invented.

Use a dense comparison layout for populated data. Keep the current exception and its decision controls prominent at narrow widths. Do not turn every record or field into an independent card.

## Product identity and scoped exception

The neutral operations system uses one deliberate cold-chain marker: a thin frost-blue rule identifies sensor-provenance information. It is not a general decorative gradient, page background, or status color. Preserve this marker on the provenance region and do not spread it to unrelated surfaces.

Status meaning continues to come from text and the approved status component, not color alone. Destructive quarantine actions continue to use the approved destructive action component.

## Reachable states

The surface supports populated, empty, data-error, and permission-denied states. A coordinator can open a source record, move focus to the quarantine action with the documented shortcut, open a confirmation dialog, cancel, or confirm. Long Danish reasons and facility names are representative content, not placeholders to shorten.

## Exemplar boundary

`design/exemplars.json` records one local comparison-pattern exemplar. Only the purpose and traits marked applicable may inform this surface. Its layout, palette, copy, assets, and implementation are not product standards and must not be copied.
