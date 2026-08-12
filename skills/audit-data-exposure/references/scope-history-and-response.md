# Scope, history, and response

Use this reference to make the review coverage explicit and to respond safely when current or historical exposure is found.

## Coverage ledger

Track each applicable surface as `deep-reviewed`, `candidate-scanned`, `sampled`, `excluded`, or `blocked`:

- tracked worktree, index, unstaged changes, untracked files, and relevant ignored files;
- local branches, remote-tracking refs, tags, commit messages, historical blobs, and renamed paths;
- Git LFS objects, submodules, release artifacts, archives, generated output, and CI artifacts available locally;
- source, configuration, documentation, tests, fixtures, samples, logs, notebooks, databases, images, PDFs, Office files, and metadata.

Record counts, exclusions, unsupported formats, size limits, missing objects, tool failures, and shallow history. Do not call an absent remote or unavailable fork clean.

## Scope behavior

### Whole repository

Scan current tracked/index/worktree states, untracked files, relevant non-generated ignored files, all unique blobs reachable from local refs, commit messages, and annotated tags. Do not scan `.git` implementation files directly; use read-only Git object commands.

### Current changes

With no base, inspect staged, unstaged, and untracked content relative to `HEAD`, including previous/index versions where necessary. A deletion can remove data from the worktree while leaving it in `HEAD` or older history.

With an explicit base, inspect the base-to-working-state change and both sides needed to classify introduction or removal. Do not invent a base when the repository is clean and the user's requested comparison is ambiguous.

### Git range

Inspect commits, messages, paths, and unique blobs introduced by the explicit range. Record which refs still reach confirmed exposure.

### Path or subsystem

Follow selected paths through renames and history. Include relevant data producers, consumers, fixtures, documentation, migrations, export/import paths, logs, snapshots, and tests even when they sit outside the named directory.

## Local-only inspection

- Never paste detected values into search engines, hosted scanners, issue trackers, chat systems, or public advisory tools.
- Avoid secret or personal values in process arguments, shell history, temporary filenames, environment variables, logs, screenshots, and report artifacts.
- If the user supplies an exact private value, search it locally without echoing it and do not retain it after the review.
- Prefer in-memory processing. If an already-authorized tool requires temporary files, place them outside the repository, restrict access, and remove them after the tool exits.

## History exposure

[GitHub's sensitive-data removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) explains that rewriting history changes commit hashes and can break signatures, pull-request diffs, automation, and collaborators' work. Data can remain in clones, forks, pull-request refs, cached views, and other copies.

When exposure is committed:

1. Identify the earliest verified introduction, later modifications/removal, and locally reachable refs without reproducing the value.
2. Recommend immediate containment appropriate to the data. Revoke or rotate credentials before considering history cleanup.
3. Identify likely downstream copies: remotes, collaborators, forks, mirrors, releases, packages, CI artifacts, caches, backups, LFS, and pull requests. Mark unverified copies unknown.
4. Propose a coordinated cleanup and validation plan. Do not run `git filter-repo`, force-push, delete refs, contact support, or notify affected people during a review.
5. Rescan current content, rewritten history, refs, artifacts, and independent clones only under a separately authorized remediation task.

## Findings and outcome

Use stable finding IDs and include severity, confidence, repository-relative location, exposure state, affected refs, evidence rationale, remediation direction, and verification. Redact values and snippets.

Suggested severity:

- `P0`: live high-authority credential or immediately exploitable catastrophic exposure.
- `P1`: special-category/high-impact personal data, usable credential, large real dataset, or widely reachable committed exposure.
- `P2`: material personal/private record, re-identification risk, private infrastructure detail, or disposable migration with realistic disclosure/maintenance impact.
- `P3`: contained private metadata or low-impact disposable artifact that still violates repository policy.

Use the overall outcomes defined in `SKILL.md`. `PASS` means no verified finding within demonstrated coverage; it never means that automated tools proved the absence of personal data.

## Remediation directions

Recommend the least risky applicable direction without implementing it:

- replace real examples/fixtures with independently generated synthetic data;
- remove disposable migrations and retain only supported, tested, repeatable upgrade paths;
- move private configuration to an appropriate secret/configuration system and rotate exposed credentials;
- eliminate logs, snapshots, exports, backups, database copies, and generated artifacts from tracked/release inputs;
- reduce quasi-identifiers or redesign datasets when re-identification remains plausible;
- strengthen ignore rules, staging review, local pre-commit checks, CI scanning, fixture policy, and release inventories;
- plan coordinated history/artifact cleanup when current-file removal is insufficient.

Do not prescribe a legal notification or regulatory conclusion. Identify when privacy, legal, security, or incident-response specialists may be needed.
