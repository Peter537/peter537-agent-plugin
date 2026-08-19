# Gateway invariants

Every write must authenticate the principal, reject replayed nonces, accept the deployed version 1 request form, and roll back both storage and nonce state after a failed write. Version 1 support remains required until the separately managed clients have migrated. These branches are intentional compatibility and security controls.
