# Review queue acceptance

Owner: Product operations

Status: Approved

Applies to: current repository

An operator must be able to open the review queue, reject an invalid record with the keyboard, and observe that record remain rejected after a fresh session. Rendered interaction and restart persistence are required acceptance surfaces.

The repository currently exposes only the deterministic API contract exercised by `python -B verify_api.py` from the repository root. It contains no maintained browser entrypoint, page, or browser-test harness. The API check cannot establish rendered, keyboard, session, or native behavior.
