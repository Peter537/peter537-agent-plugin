---
name: audit-data-exposure
description: Perform read-only, redacted reviews of repositories, Git changes or ranges, paths, and subsystems for personal data, private records, credentials, developer-machine metadata, re-identifiable samples, anonymization failures, and disposable one-time migrations or conversions. Use only when the user explicitly requests a personal-data, privacy, anonymization, repository-leak, sensitive-data exposure, or disposable-migration review. Do not invoke merely because code is being committed, released, published, or open-sourced, and do not use for ordinary code audits, dependency reviews, performing dataset anonymization, legal-compliance opinions, or implementation work.
license: MIT
---

# Repository Data Exposure Review

Audit repository exposure without transmitting, reproducing, changing, or deleting the data under review. Treat automation as candidate discovery, not proof that data is safe or anonymous.

## Preserve the review boundary

- Remain read-only. Do not sanitize files, rotate credentials, rewrite Git history, delete artifacts, contact third parties, or save a report unless separately authorized.
- Keep repository content, detected values, private paths, manifests, history, and reports local. Do not submit them to websites, hosted scanners, models, registries, or other external services.
- Never print, quote, hash, or include surrounding text for a detected value. Report only the repository-relative location, category, confidence, exposure state, and remediation direction.
- Record `git status --short` before and after the review. Stop and report any unexpected tracked-file mutation caused by a command.
- Use only repository-provided or already-installed read-only tools. Do not install detectors, dependencies, models, OCR packages, or Git history-rewrite utilities.
- Do not claim legal compliance, regulatory certification, penetration testing, irreversible anonymization, or a guarantee that no personal data exists.

## Read the focused references

- Read [data-classification-and-signals.md](references/data-classification-and-signals.md) before classifying personal/private data, public attribution, synthetic examples, re-identification risk, or migration artifacts.
- Read [scope-history-and-response.md](references/scope-history-and-response.md) before selecting Git scope, interpreting coverage gaps, reporting committed exposure, or recommending remediation.

## Establish scope and repository truth

1. Read all applicable repository instructions.
2. Record Git status, repository root, remotes without embedded credentials, shallow-clone state, local branches, remote-tracking refs, tags, submodules, Git LFS use, and ignored/generated directory conventions.
3. Establish intentional public identities from repository evidence: repository owner or organization, manifest authors, public support contacts, license attribution, project URLs, and ordinary contributor metadata. Do not infer that unrelated details are permitted merely because they appear online.
4. Inventory source, documentation, configuration, tests, fixtures, examples, logs, dumps, databases, notebooks, archives, Office documents, PDFs, images, media metadata, generated artifacts, CI artifacts, and data-shaped ignored files.
5. Identify product-maintained schema migrations and supported import/export paths separately from apparently disposable migrations, converters, backfills, repair scripts, and temporary data tools.

## Select the review scope

- **Whole repository:** inspect current tracked content, index state, unstaged content, untracked files, relevant non-generated ignored files, commit messages, annotated tags, and unique blobs reachable from every local branch, remote-tracking ref, and tag.
- **Current Git changes:** inspect staged, unstaged, and untracked content relative to `HEAD`, including previous content for changed or removed files. Use an explicit base when supplied.
- **Git range:** inspect every unique blob and commit message introduced by the explicit range plus both sides of changed content needed to judge removal or persistence.
- **Path or subsystem:** inspect current selected paths, their reachable history and renames, and relevant producers, consumers, fixtures, documentation, and migration utilities.

Never fetch missing refs automatically. Mark a shallow clone, unavailable LFS object, uninitialized or unscanned submodule, unsupported archive, missing remote ref, or unavailable historical object as a coverage gap.

## Run deterministic candidate discovery

Run the bundled scanner from the target repository with the appropriate scope:

```text
python <skill-path>/scripts/scan_repository_data_exposure.py --root . --scope full
python <skill-path>/scripts/scan_repository_data_exposure.py --root . --scope changes
python <skill-path>/scripts/scan_repository_data_exposure.py --root . --scope changes --base <ref>
python <skill-path>/scripts/scan_repository_data_exposure.py --root . --scope history --range <range>
python <skill-path>/scripts/scan_repository_data_exposure.py --root . --scope path --path <path>
```

The scanner uses standard-library code and read-only Git commands. It emits JSON containing detector categories and locations, never values or snippets. Preserve its complete coverage and gap summary. Do not pass private search terms on a command line.

Use already-installed secret, PII, metadata, archive, OCR, or database inspection tools only when their execution is demonstrably local, read-only, non-uploading, and non-executing. Record tool version and configuration. A clean result covers only that tool's recognizers and supported formats.

## Validate candidates locally

1. Inspect each candidate at its local source without copying its value into notes, commands, prompts, or the final report.
2. Distinguish intentionally public attribution, clearly reserved synthetic examples, and product-supported generic migrations from actual exposure.
3. Evaluate combinations of quasi-identifiers and external linkage. Pseudonyms, hashes, tokens, truncated values, or removed direct identifiers do not establish irreversible anonymization.
4. Treat every apparently disposable one-time migration or conversion as a finding even if no literal private value is embedded. Do not classify a maintained repeatable schema migration, supported upgrade path, reusable import/export tool, or fixture generator as disposable solely because it transforms data.
5. Determine whether a finding exists only in current uncommitted content, in the index, in `HEAD`, or in reachable history and which refs preserve it.
6. Classify unsupported binaries, images, PDFs, databases, encrypted archives, missing LFS objects, and unscanned submodules as gaps rather than silent passes.

## Decide the outcome

- `PASS`: no verified exposure or disposable migration and no critical coverage gap.
- `PASS_WITH_WARNINGS`: no confirmed finding, but lower-confidence candidates or non-critical gaps remain.
- `FAIL`: confirmed unauthorized personal/private data, credential exposure, re-identifiable data presented as anonymous, or any disposable one-time migration.
- `BLOCKED`: critical scope cannot be inspected safely or a high-confidence candidate cannot be resolved.

A `PASS` remains limited to the reviewed scope and methods. Never turn it into a guarantee.

## Report without leaking

Lead with the coverage ledger, then the outcome and redacted findings. For each finding include:

- stable ID, category, severity, confidence, and disposition;
- repository-relative path plus line, commit, ref, or archive-member location as applicable;
- current, index, untracked, ignored, or historical exposure state;
- why the item is not permitted public metadata or safe synthetic content;
- introduction/removal evidence and whether reachable history still contains it;
- remediation direction and a verification method, without reproducing the value.

Also report excluded and blocked surfaces, scanner/tool commands, unexpected mutations, and the final Git status comparison. If no finding survives validation, say so while preserving coverage limitations.

For committed exposure, recommend containment and coordinated cleanup but do not execute it. For credentials, recommend revocation or rotation before history cleanup. Explain that clones, forks, pull-request refs, cached commit views, LFS storage, release artifacts, and mirrors may retain data after current files change.
