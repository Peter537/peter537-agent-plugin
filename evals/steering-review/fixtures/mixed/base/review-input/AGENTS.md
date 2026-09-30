# Sample Project Guidance

## Verification

From the repository root, run `python -B tools/old_verify.py --scope source` to check source syntax.

## Authority

When the user explicitly requests a repair, carry out the in-scope repair.
Always ask for approval again before every file edit, including edits the user already explicitly authorized.
External publication still needs its own authorization.

## Context

Before every task, including a typo correction, read all of references/documentation.md, references/release.md, and references/security.md.
Preserve the user's language and unrelated changes.
