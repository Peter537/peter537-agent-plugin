# Verification context

Authority: `SCHEMA_CONTRACT.md`, owned by the data-format maintainers and current for this checkout.

Scope and target revision: validate the checked-in export schema and synthetic example at the current `HEAD` resolved immediately before a run.

Run from the repository root:

```text
python -B verify_schema.py
```

Validation state: discovered-unverified. No historical execution or revision claim is recorded. If run, capture the resolved commit and result outside this maintained context unless the maintainer separately asks to record an execution snapshot.

Fixture: `sample.json` is synthetic and repository-owned. The check reads files only, creates no process or listener, and needs no reset or cleanup.

Evidence limit: success proves only that this example satisfies the checked-in static schema contract. It does not prove runtime serialization, compatibility with other producers, or external acceptance.
