# Verification facts

This file is authoritative for the accompanying maintainer note.

- Release: `v2.4.0`.
- Command: `python -B tools/check_release.py --strict`.
- Timeout: 30 seconds.
- Results: `PASS`, `FAIL`, and `BLOCKED`.
- Output: `artifacts/verification.json`.
- Maintainer reference: [verification runbook](https://example.invalid/maintainers/verification).
- The command has been exercised on Linux. Windows behaviour remains unverified.
- The output is captured before the temporary directory is removed.
