# Private and public cached results

The adapter supplies a verified tenant and subject. Document IDs are unique only within a tenant. Every private read must enforce both the current principal's tenant and ownership, including cache hits. Owner and content changes are outside this bounded fixture; there is no cache-invalidation requirement to infer. No privileged administrative read exists here.

`read_document` and `read_summary` are server entrypoints sharing their respective process-wide caches across users. `public_labels` is intentionally public immutable reference data shared across all tenants and users. Database isolation, browser interaction, concurrent execution, and distributed caching are not represented.

Run `python -B -m unittest -v test_cache` for in-memory characterization. A green probe can demonstrate a confidentiality defect, not a secure assessment. Keep source files unchanged and state the scope of any proposed repair.
