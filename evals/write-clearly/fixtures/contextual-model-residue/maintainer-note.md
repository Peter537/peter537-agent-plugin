# Verification update

Absolutely—here is the maintainer note you asked for. I have put together a complete and helpful explanation of the verification update.

## What this exciting change does

This powerful, robust, and reliable improvement transforms release checking into a truly significant capability. It is not merely a script; it is a comprehensive foundation for confidence.

For `v2.4.0`, run `python -B tools/check_release.py --strict`. The command stops after 30 seconds.

The result is one of three states:

- `PASS`: the required checks completed successfully.
- `FAIL`: trustworthy evidence contradicted a requirement.
- `BLOCKED`: required evidence was unavailable.

The output is captured in `artifacts/verification.json` before the temporary directory is removed. Capture comes before cleanup—the report must remain available for review.

The command has been exercised on Linux. Windows behaviour remains unverified, so the result may not describe Windows. See the [verification runbook](https://example.invalid/maintainers/verification).

## Why this matters

This gives maintainers a clear, comprehensive, and complete way to understand release readiness. In other words, the command runs the required checks, produces one of the three result states, and writes the report before cleanup.

## In summary

To summarise, maintainers run the strict command for `v2.4.0`, wait no more than 30 seconds, read `PASS`, `FAIL`, or `BLOCKED`, and review `artifacts/verification.json`. This important improvement creates a stronger and brighter future for every release.

Thanks for taking the time to read this update.
