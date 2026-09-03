# Provider Contract v2 limits

Owner: Provider Integration

Effective: 2026-08-01

Applies to: Provider v2 bulk-upload endpoint for the target release

- Maximum request size: 80 record IDs.
- Maximum in-flight requests: one per account.
- A rejected request applies no records.
- A successful request preserves the supplied record order.

Provider Integration confirmed this contract during approval of `REQUIREMENTS.md`.
