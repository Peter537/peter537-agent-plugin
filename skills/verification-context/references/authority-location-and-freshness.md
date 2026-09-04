# Authority, location, and freshness

## Select a durable home

Search repository instructions, contributor guidance, maintained documentation, CI configuration, project manifests, and existing verification notes before proposing a location. Prefer a location that already owns project operations and is discoverable to both maintainers and automated agents.

Treat a file's existence as weak evidence. Establish:

- a named or repository-evidenced owner;
- the audience and scope;
- the revision, platform, or product variant it governs;
- its relationship to stronger authorities such as accepted requirements, tests, build configuration, and CI;
- whether newer evidence contradicts it.

GitHub documents repository contributor guidance as durable project material that can live in the repository root, `docs`, or `.github`; this supports repository-owned context without prescribing a universal filename: <https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors>.

If no clear home exists, ask the user to approve one exact path. If two current owners conflict, do not merge them by guesswork; identify the conflicting claims and request an owner decision.

## Classify freshness precisely

- `verified-current`: the documented item was exercised safely against the stated target during this task.
- `discovered-unverified`: current repository evidence declares the item, but it was not run.
- `stale`: a newer authority or direct repository evidence contradicts the item.
- `blocked`: the required source, target identity, permission, or reset boundary is unavailable.

A passing historical CI record is current only for its exact revision and environment. A command found in prose is not verified merely because it looks plausible. A dirty worktree is a distinct target; do not label its observations with `HEAD` alone.

## Preserve acceptance authority

Verification context explains how to gather evidence. It does not decide what the product must do. Link acceptance criteria to their owning requirements, issue, contract, test, or decision record and preserve conflicts rather than silently rewriting them.
