# Read-only project directory

This is a bounded review of the browser configuration and the server read handler. The fixture contains no writes, local password store, uploads, or HTML rendering. Authentication is provided by a separately managed identity provider. The HTTP adapter verifies the token's signature, issuer, audience, and expiration before passing the principal to `list_projects`; that adapter and its runtime verification are outside this fixture.

The database is private and reachable only from the server. Object authorization is enforced by the handler. Database RLS is not part of this architecture. The browser publishable identifier is intentionally public and grants no privileged access. Its presence is not evidence of a secret leak.

External TLS, authentication-provider settings, encryption at rest, key management, and gateway quotas cannot be inspected here. Report that assurance boundary without inventing vulnerabilities or claiming production is secure. No live access is authorized.
