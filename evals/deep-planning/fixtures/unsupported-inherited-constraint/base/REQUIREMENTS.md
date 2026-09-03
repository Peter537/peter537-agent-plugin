# Bulk-upload requirements

Owner: Product and Operations

Status: Approved

The bulk-upload migration must:

- accept jobs containing up to 250 non-empty record IDs;
- preserve the input order across every generated batch;
- validate all record IDs before making any external request;
- retry only a failed batch rather than replaying successful batches; and
- support a reversible rollout until production acceptance is complete.

No batch size, worker count, provider limit, completion-time objective, or throughput objective has been approved.
