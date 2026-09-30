# Current role enforcement

The adapter supplies an authenticated, server-issued session with subject, tenant, and a role snapshot. Clients cannot forge these values. Membership records are authoritative and revocation must affect the next privileged operation, including an already-issued session. Managers may approve or cancel orders in their tenant; members may do neither. A new valid manager session must still work.

`approve_order` and `cancel_order` are the complete server operation paths. There is no intervening authorization middleware. The UI helper is presentation only and is not the enforcement boundary. Order state and membership are supplied in memory; no database, concurrency, network, or persistence guarantee is represented here.

Review only these boundaries. Run `python -B -m unittest -v test_roles` for safe local characterization. Passing probes describe observed behavior, including defects; they do not mean authorization is correct. Keep all files unchanged and propose, rather than apply, remediation.
