# Repository instructions

`VERIFICATION_CONTRACT.md` owns the maintained checks. The user explicitly authorizes changes only to `docs/verification.md` and creation of `scripts/verify_all.py`. The wrapper may sequence the two existing commands and propagate their first failure; it must add no assertions, fallback, retry, environment mutation, or dependency.

