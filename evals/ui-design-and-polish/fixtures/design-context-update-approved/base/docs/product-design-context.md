---
owner: Fulfilment Product Council
status: approved
scope: dispatch-console
last_reviewed: 2026-04-10
---

# Dispatch console design context

Operators assign shipments from a dense comparison queue. British English is the default locale.

Use tokens `--panel-bg`, `--warning-red`, and `--spacing-sm` from `styles/tokens.css`. Use the `RouteBadge` component described in `components/route-badge.md`.

The approved amber route-risk rail is limited to the comparison column. Its purpose is to keep risk evidence visually anchored while operators scan rows.

The web and tablet interfaces use identical density. Error and permission states are documented by the component source.

Internal exemplar `EXP-011` may inform evidence grouping, but its palette and layout must not be copied.
