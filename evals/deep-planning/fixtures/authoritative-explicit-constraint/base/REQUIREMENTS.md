# Approved uploader requirements

Owner: Integration Platform Council

Approved: 2026-08-15

Scope: Provider v2 bulk-upload adapter

These requirements were validated with the Provider Integration owner for the target release:

- send no more than 80 record IDs in one provider request because Provider Contract v2 rejects larger requests;
- allow exactly one in-flight provider request per account because Provider Contract v2 permits no concurrent requests for that account;
- validate every non-empty record ID before the first provider request;
- preserve record order across requests; and
- retry only a failed request.

The request-size and concurrency constraints are approved interface requirements, not provisional tuning values. Their rationale and current provider authority are recorded in `PROVIDER_CONTRACT.md`.
