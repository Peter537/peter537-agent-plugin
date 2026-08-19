# Exception triage

Warehouse coordinators need to review scan exceptions without leaving the existing shell. Show the package identifier, checkpoint, age, reason, and source facility. The default order is oldest first.

The surface must provide loading, empty, offline, error, and populated states. A coordinator can assign an exception to themselves, open its event history, or mark it resolved. Resolving requires a confirmation that names the package identifier. The offline state must disable mutations without hiding the last known data.

Reuse the shell's navigation labels, `data-testid` naming style, two-column desktop rhythm, and single-column narrow layout. Do not invent backend calls; deterministic fixture data is sufficient.
