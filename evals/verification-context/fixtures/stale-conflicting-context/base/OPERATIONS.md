# Export verification contract

Owner: export-service maintainers

Status: current

Revision scope: the current repository checkout, identified by `EXPORT_CONTRACT_REVISION`.

Run the maintained local check from the repository root:

```text
python -B verify_export.py
```

The check verifies deterministic creation of a synthetic local export and exact cleanup of its task-owned temporary directory. A downstream remote-delivery objective appears in the stale note, but it has no current decision owner, endpoint contract, delivery guarantee, or approved verification method. That claim remains unresolved and must not be inferred from the local check.
