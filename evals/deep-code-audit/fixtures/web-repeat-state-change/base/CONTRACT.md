# Retried inventory operations

An authenticated member may reserve or release stock in their own tenant. The adapter supplies a verified subject and tenant. Both operations promise one effect per `(tenant, subject, operation type, operation ID)` during this in-memory session. A repeat of the same payload returns the original result; a reused ID with a different payload must be rejected. Distinct IDs and different members or tenants remain independent operations.

The adapter passes retries directly to these functions and performs no deduplication. Stock and receipts are process-local synthetic state; restarts, concurrent execution, durable transactions, billing, and external systems are outside this contract. Ordinary reads are not required to have replay keys.

Run `python -B -m unittest -v test_inventory` to characterize the paths without file writes. Successful characterization can demonstrate a violation. Report implementable recommendations and preserved behavior; do not repair the fixture.
