# Review-service verification authority

Owner: Review service maintainers

Status: Current

Applies to: current repository

The local public contract is checked from the repository root with `python -B verify_public_contract.py`. Credentialed remote verification, when separately authorized for a named non-production target, requires the `reviewer` test role and the `REVIEW_SERVICE_TEST_TOKEN` environment variable supplied by the organisation secret store. The value must never be written to the repository or a report.

Use only `fixtures/synthetic-review.json`. Browser sessions, cookies, request headers, private target addresses, and real customer records are not durable verification context. Remote availability, authenticated authorization, and production behavior remain unverified by the local check.
