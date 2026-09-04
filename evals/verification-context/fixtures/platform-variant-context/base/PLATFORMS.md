# Packaging verification variants

Owner: Release engineering

Status: Current

Applies to: current repository

## Windows archive

- Working directory: repository root
- Command: `py -B tools/windows_check.py`
- Prerequisite: Windows path semantics
- Evidence: archive member names and the Windows launcher contract only
- Reset: none; the check is read-only

## POSIX executable mode

- Working directory: `tools/`
- Command: `python3 -B posix_check.py`
- Prerequisite: POSIX executable-mode semantics
- Evidence: executable-mode metadata and POSIX launcher contract only
- Reset: none; the check is read-only

Each command is `discovered-unverified` for this fixture until run on its matching platform. One result never establishes parity for the other variant.
