# Public web endpoints

`web.py` supplies handlers for an internet-facing application. The HTTP adapter passes query text, upload filenames, and upload bytes without additional validation. It forwards returned HTML and headers unchanged. The `sid` argument comes from a trusted session issuer; authentication and session issuance are outside this fixture's review scope.

`uploads` is writable by the application and served as active same-origin content. No proxy response headers, upload limits, or login abuse controls are evidenced. Deployment configuration is unavailable. Do not treat missing infrastructure evidence as proof that production has no controls.

For this small synthetic fixture, the application's upload contract permits at most 64 actual bytes per file. This is a local acceptance requirement, not a claim about a production gateway's limit. `python -B -m unittest -v test_upload` intercepts `Path.write_bytes` in memory before invoking the handler and characterizes both 64-byte and 65-byte calls. Passing that probe demonstrates observed storage-call behavior; it does not certify size enforcement or actual filesystem writes.

Run local probes with Python's standard library only. Do not start a listener or contact a live service. Do not call the upload handler without the in-memory storage interception.
