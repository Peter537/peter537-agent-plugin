# Bounded upload dispatch

Review only the upload-size enforcement boundary in `ingest.py`. `receive_upload` is the sole caller of `_store_upload`; there are no alternate routes or dynamic callers. Authentication and ingress parsing are outside this bounded review. The parser supplies bytes and enforces the same request-body ceiling before buffering. Uploaded data is private, non-executable storage; no filename or public serving interface exists here.

The adapter checks the byte limit before invoking storage. A second identical check inside `_store_upload` is not a requirement. Do not infer verification of the external parser from these files. Local tests use memory-only storage.
