from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCANNER = REPOSITORY_ROOT / "skills" / "audit-data-exposure" / "scripts" / "scan_repository_data_exposure.py"


def load_scanner_module():
    specification = importlib.util.spec_from_file_location("data_exposure_scanner", SCANNER)
    if specification is None or specification.loader is None:
        raise RuntimeError("Cannot load data-exposure scanner module.")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


scanner_module = load_scanner_module()


def temporary_directory() -> tempfile.TemporaryDirectory[str]:
    return tempfile.TemporaryDirectory(prefix="audit-data-exposure-test-")


def git_environment() -> dict[str, str]:
    environment = {
        name: value for name, value in os.environ.items() if not name.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
            "GIT_AUTHOR_EMAIL": "fixture@localhost",
            "GIT_AUTHOR_NAME": "Data Exposure Fixture",
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
            "GIT_COMMITTER_EMAIL": "fixture@localhost",
            "GIT_COMMITTER_NAME": "Data Exposure Fixture",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CREDENTIAL_INTERACTIVE": "never",
            "GIT_LFS_SKIP_SMUDGE": "1",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def run_git(repository: Path, *arguments: str, input_text: str | None = None) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgSign=false",
            "-c",
            "tag.gpgSign=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            "-c",
            "core.autocrlf=false",
            "-c",
            "protocol.allow=never",
            "-c",
            "user.useConfigOnly=true",
            *arguments,
        ],
        cwd=repository,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=git_environment(),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout


def write_file(repository: Path, relative: str, content: str | bytes) -> None:
    destination = repository / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        destination.write_bytes(content)
    else:
        destination.write_text(content, encoding="utf-8")


def initialize_repository(repository: Path, files: dict[str, str | bytes] | None = None) -> None:
    repository.mkdir(parents=True)
    run_git(repository, "init", "--quiet", "--initial-branch=main", "--template=")
    for relative, content in (files or {"README.md": "Fixture\n"}).items():
        write_file(repository, relative, content)
    run_git(repository, "add", "--all")
    run_git(repository, "commit", "--quiet", "-m", "Base fixture")


def commit_all(repository: Path, message: str) -> str:
    run_git(repository, "add", "--all")
    run_git(repository, "commit", "--quiet", "-m", message)
    return run_git(repository, "rev-parse", "HEAD").strip()


def run_scanner(
    repository: Path,
    *arguments: str,
    inherited_git_environment: dict[str, str] | None = None,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    environment = git_environment()
    if inherited_git_environment:
        environment.update(inherited_git_environment)
    result = subprocess.run(
        [sys.executable, str(SCANNER), "--root", str(repository), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=environment,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"Scanner did not emit JSON: {result.stdout!r} {result.stderr!r}") from exc
    return result, payload


def create_fsmonitor_hook(directory: Path) -> tuple[Path, Path]:
    marker = directory / "fsmonitor-invoked.txt"
    if os.name == "nt":
        hook = directory / "fsmonitor.cmd"
        hook.write_text(
            f'@echo off\r\necho invoked>>"{marker}"\r\necho /\r\n',
            encoding="ascii",
        )
    else:
        hook = directory / "fsmonitor.sh"
        hook.write_text(
            "#!/bin/sh\n"
            f"printf invoked >> {shlex.quote(str(marker))}\n"
            "printf '/\\n'\n",
            encoding="utf-8",
        )
        hook.chmod(0o700)
    return hook, marker


def repository_snapshot(repository: Path) -> tuple[str, dict[str, str]]:
    status = run_git(repository, "status", "--porcelain=v1", "--untracked-files=all")
    files: dict[str, str] = {}
    for path in repository.rglob("*"):
        if not path.is_file() or ".git" in path.relative_to(repository).parts:
            continue
        files[path.relative_to(repository).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return status, files


def categories(payload: dict[str, object], collection: str = "candidates") -> set[str]:
    records = payload.get(collection, [])
    assert isinstance(records, list)
    return {str(record["category"]) for record in records if isinstance(record, dict)}


class ScannerTests(unittest.TestCase):
    maxDiff = None

    def test_full_scope_scans_packages_vscode_and_relevant_ignored_data(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            initialize_repository(repository, {".gitignore": "ignored-data/\n", "README.md": "Fixture\n"})
            tokens = [f"person-{secrets.token_hex(10)}@example.invalid" for _ in range(3)]
            write_file(repository, "packages/core/record.txt", tokens[0] + "\n")
            write_file(repository, ".vscode/session.txt", tokens[1] + "\n")
            write_file(repository, "ignored-data/export.txt", tokens[2] + "\n")
            run_git(repository, "add", "--force", "packages/core/record.txt", ".vscode/session.txt")
            run_git(repository, "commit", "--quiet", "-m", "Add fixture surfaces")

            result, payload = run_scanner(repository, "--scope", "full")

            self.assertEqual(result.returncode, 0)
            paths = {record.get("path") for record in payload["candidates"]}
            self.assertIn("packages/core/record.txt", paths)
            self.assertIn(".vscode/session.txt", paths)
            self.assertIn("ignored-data/export.txt", paths)
            excluded = {record.get("path") for record in payload["exclusions"]}
            self.assertNotIn("packages/core/record.txt", excluded)
            self.assertNotIn(".vscode/session.txt", excluded)
            for token in tokens:
                self.assertNotIn(token, result.stdout)
                self.assertNotIn(token, result.stderr)

    def test_path_scope_rejects_unsafe_repository_paths_without_echoing_them(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            initialize_repository(repository)
            unsafe_values = ["../outside.txt", str((repository.parent / "outside.txt").resolve()), ".git/config"]
            for value in unsafe_values:
                with self.subTest(value=value):
                    result, payload = run_scanner(repository, "--scope", "path", "--path", value)
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(payload.get("error"), "ValueError")
                    self.assertNotIn(value, result.stdout)
                    self.assertNotIn(value, result.stderr)

    def test_index_symlink_is_an_explicit_gap(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            initialize_repository(repository)
            blob = run_git(repository, "hash-object", "-w", "--stdin", input_text="../private-target\n").strip()
            run_git(repository, "update-index", "--add", "--cacheinfo", f"120000,{blob},linked.txt")
            run_git(repository, "commit", "--quiet", "-m", "Add symbolic link fixture")

            result, payload = run_scanner(repository, "--scope", "full")

            self.assertEqual(result.returncode, 0)
            self.assertIn("symlink-target-not-inspected", categories(payload, "gaps"))
            self.assertFalse(any(record.get("path") == "linked.txt" for record in payload["candidates"]))

    def test_physical_symlink_is_not_followed(self) -> None:
        with temporary_directory() as temporary:
            root = Path(temporary)
            repository = root / "repo"
            initialize_repository(repository)
            token = f"outside-{secrets.token_hex(12)}@example.invalid"
            outside = root / "outside.txt"
            outside.write_text(token + "\n", encoding="utf-8")
            link = repository / "physical-link.txt"
            try:
                link.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"Symbolic links are unavailable: {type(exc).__name__}")
            run_git(repository, "add", "physical-link.txt")
            run_git(repository, "commit", "--quiet", "-m", "Add physical link fixture")

            result, payload = run_scanner(repository, "--scope", "full")

            self.assertEqual(result.returncode, 0)
            self.assertIn("symlink-or-reparse-target-not-inspected", categories(payload, "gaps"))
            self.assertNotIn(token, result.stdout)
            self.assertNotIn(token, result.stderr)

    def test_path_scope_excludes_unrelated_commit_and_tag_metadata(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            initialize_repository(repository, {"selected.txt": "Safe selected content\n"})
            write_file(repository, "unrelated.txt", "Safe unrelated content\n")
            commit_all(repository, "one-off personal migration for unrelated data")
            run_git(repository, "tag", "-a", "metadata-fixture", "-m", "delete after personal backfill")

            result, payload = run_scanner(
                repository, "--scope", "path", "--path", "selected.txt"
            )

            self.assertEqual(result.returncode, 0)
            metadata_scopes = {"commit-message", "annotated-tag", "tagger"}
            self.assertFalse(any(record.get("scope") in metadata_scopes for record in payload["candidates"]))

            full_result, full_payload = run_scanner(repository, "--scope", "full")
            self.assertEqual(full_result.returncode, 0)
            self.assertTrue(any(record.get("scope") == "commit-message" for record in full_payload["candidates"]))
            self.assertTrue(any(record.get("scope") == "annotated-tag" for record in full_payload["candidates"]))

    def test_path_history_follows_renames_and_resolves_redacted_locations(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            token = f"record-{secrets.token_hex(12)}@example.invalid"
            old_path = "records/person@example.invalid.txt"
            shared = "schema: fixture-v1\nstatus: synthetic\nowner: evaluation\n"
            initialize_repository(repository, {old_path: token + "\n" + shared})
            introducing_commit = run_git(repository, "rev-parse", "HEAD").strip()
            (repository / "selected").mkdir()
            run_git(repository, "mv", old_path, "selected/current.txt")
            write_file(repository, "selected/current.txt", "Synthetic fixture only\n" + shared)
            commit_all(repository, "Rename and sanitize fixture")

            result, payload = run_scanner(
                repository, "--scope", "path", "--path", "selected/current.txt"
            )

            self.assertEqual(result.returncode, 0)
            historical = [
                record
                for record in payload["candidates"]
                if record.get("scope") == "history" and record.get("category") == "email-address"
            ]
            self.assertTrue(historical)
            self.assertTrue(any(record.get("commit") == introducing_commit for record in historical))
            self.assertTrue(any("<redacted-name>" in str(record.get("path")) for record in historical))
            self.assertNotIn(token, result.stdout)
            self.assertNotIn("person@example.invalid", result.stdout)

    def test_changes_scope_inspects_pre_rename_content(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            token = f"old-{secrets.token_hex(12)}@example.invalid"
            initialize_repository(repository, {"private/old.txt": token + "\n"})
            (repository / "current").mkdir()
            run_git(repository, "mv", "private/old.txt", "current/new.txt")
            write_file(repository, "current/new.txt", "Synthetic fixture only\n")

            result, payload = run_scanner(repository, "--scope", "changes")

            self.assertEqual(result.returncode, 0)
            self.assertTrue(
                any(
                    record.get("scope") == "changes-base"
                    and record.get("path") == "private/old.txt"
                    and record.get("category") == "email-address"
                    for record in payload["candidates"]
                )
            )
            self.assertNotIn(token, result.stdout)

    def test_changes_scope_covers_staged_unstaged_untracked_and_removed_content(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            removed_token = f"removed-{secrets.token_hex(10)}@example.invalid"
            initialize_repository(
                repository,
                {
                    "unstaged.txt": "Safe\n",
                    "staged.txt": "Safe\n",
                    "removed.txt": removed_token + "\n",
                },
            )
            tokens = [f"change-{secrets.token_hex(10)}@example.invalid" for _ in range(3)]
            write_file(repository, "unstaged.txt", tokens[0] + "\n")
            write_file(repository, "staged.txt", tokens[1] + "\n")
            run_git(repository, "add", "staged.txt")
            write_file(repository, "untracked.txt", tokens[2] + "\n")
            (repository / "removed.txt").unlink()
            before = repository_snapshot(repository)

            result, payload = run_scanner(repository, "--scope", "changes")

            self.assertEqual(result.returncode, 0)
            located = {(record.get("scope"), record.get("path")) for record in payload["candidates"]}
            self.assertIn(("changes-worktree", "unstaged.txt"), located)
            self.assertIn(("changes-worktree", "staged.txt"), located)
            self.assertIn(("changes-worktree", "untracked.txt"), located)
            self.assertIn(("index", "staged.txt"), located)
            self.assertIn(("index", "removed.txt"), located)
            self.assertEqual(repository_snapshot(repository), before)
            for token in [removed_token, *tokens]:
                self.assertNotIn(token, result.stdout)
                self.assertNotIn(token, result.stderr)

    def test_changes_scope_with_explicit_base_inspects_base_content(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            token = f"base-{secrets.token_hex(12)}@example.invalid"
            initialize_repository(repository, {"record.txt": token + "\n"})
            base = run_git(repository, "rev-parse", "HEAD").strip()
            write_file(repository, "record.txt", "Synthetic fixture only\n")
            commit_all(repository, "Sanitize fixture")

            result, payload = run_scanner(
                repository, "--scope", "changes", "--base", base
            )

            self.assertEqual(result.returncode, 0)
            self.assertTrue(
                any(
                    record.get("scope") == "changes-base"
                    and record.get("path") == "record.txt"
                    and record.get("category") == "email-address"
                    for record in payload["candidates"]
                )
            )
            self.assertNotIn(token, result.stdout)

    def test_history_range_is_scanned_without_mutating_repository(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            token = f"history-{secrets.token_hex(12)}@example.invalid"
            initialize_repository(repository, {"record.txt": token + "\n"})
            first = run_git(repository, "rev-parse", "HEAD").strip()
            write_file(repository, "record.txt", "Synthetic fixture only\n")
            commit_all(repository, "Sanitize fixture")
            before = repository_snapshot(repository)

            result, payload = run_scanner(repository, "--scope", "history", "--range", first)
            range_result, range_payload = run_scanner(
                repository,
                "--scope",
                "history",
                "--range",
                f"{first}..HEAD",
            )

            self.assertEqual(result.returncode, 0)
            self.assertEqual(range_result.returncode, 0)
            self.assertIn("email-address", categories(payload))
            self.assertIn("email-address", categories(range_payload))
            self.assertEqual(repository_snapshot(repository), before)
            self.assertNotIn(token, result.stdout)
            self.assertNotIn(token, range_result.stdout)

    def test_history_enumeration_uses_one_raw_log_not_per_commit_trees(self) -> None:
        arguments = argparse.Namespace(root=".")
        scanner = scanner_module.Scanner(arguments)
        object_id = "a" * 40
        raw_record = f":000000 100644 {'0' * 40} {object_id} A\0file.txt\0"
        calls: list[tuple[str, ...]] = []

        def fake_git_text(*git_arguments: str, check: bool = True) -> str:
            calls.append(git_arguments)
            return raw_record

        with mock.patch.object(scanner, "git_text", side_effect=fake_git_text):
            records = scanner.object_records("--all", set())

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "log")
        self.assertNotIn("ls-tree", calls[0])
        self.assertEqual(records, [(object_id, "file.txt", "100644", "blob")])

    def test_unsafe_revision_is_rejected_without_becoming_a_git_option(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            initialize_repository(repository)

            result, payload = run_scanner(
                repository, "--scope", "history", "--range=--all"
            )

            self.assertEqual(result.returncode, 2)
            self.assertEqual(payload.get("error"), "ValueError")

    def test_zip_text_is_redacted_and_archive_limits_are_explicit(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            initialize_repository(repository)
            token = f"archive-{secrets.token_hex(12)}@example.invalid"
            archive_path = repository / "evidence.docx"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("word/private.txt", token + "\n")
            commit_all(repository, "Add archive fixture")

            result, payload = run_scanner(
                repository, "--scope", "path", "--path", "evidence.docx"
            )
            self.assertEqual(result.returncode, 0)
            self.assertTrue(any(record.get("member") == "word/private.txt" for record in payload["candidates"]))
            self.assertNotIn(token, result.stdout)

            limited_result, limited_payload = run_scanner(
                repository,
                "--scope",
                "path",
                "--path",
                "evidence.docx",
                "--max-archive-member-bytes",
                "8",
            )
            self.assertEqual(limited_result.returncode, 0)
            self.assertIn("oversized-archive-member", categories(limited_payload, "gaps"))
            self.assertNotIn(token, limited_result.stdout)

    def test_archive_member_count_total_ratio_and_traversal_are_bounded(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            initialize_repository(repository)
            token = f"archive-{secrets.token_hex(12)}@example.invalid"
            archive_path = repository / "bounded.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("first.txt", "aaaaaa")
                archive.writestr("second.txt", "bbbbbb")
                archive.writestr("../../outside.txt", token + "\n" + "x" * 200)
                archive.writestr("media/image.png", b"\x89PNG\r\n\x1a\nfixture")
            commit_all(repository, "Add bounded archive fixture")
            outside = repository.parent / "outside.txt"

            count_result, count_payload = run_scanner(
                repository,
                "--scope",
                "path",
                "--path",
                "bounded.zip",
                "--max-archive-members",
                "1",
            )
            self.assertEqual(count_result.returncode, 0)
            self.assertIn("archive-member-limit", categories(count_payload, "gaps"))

            total_result, total_payload = run_scanner(
                repository,
                "--scope",
                "path",
                "--path",
                "bounded.zip",
                "--max-archive-total-bytes",
                "8",
            )
            self.assertEqual(total_result.returncode, 0)
            self.assertIn("archive-expanded-size-limit", categories(total_payload, "gaps"))

            ratio_result, ratio_payload = run_scanner(
                repository,
                "--scope",
                "path",
                "--path",
                "bounded.zip",
                "--max-compression-ratio",
                "1",
            )
            self.assertEqual(ratio_result.returncode, 0)
            self.assertIn("archive-compression-ratio-limit", categories(ratio_payload, "gaps"))
            self.assertIn("unsupported-archive-member-format", categories(ratio_payload, "gaps"))
            self.assertFalse(outside.exists())
            for result in (count_result, total_result, ratio_result):
                self.assertNotIn(token, result.stdout)
                self.assertNotIn(token, result.stderr)

    def test_history_deduplicates_identical_blobs_and_output_is_stable(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            shared = "Synthetic identical content\n"
            initialize_repository(repository, {"a.txt": shared, "person@example.invalid.txt": shared})

            first_result, first_payload = run_scanner(repository, "--scope", "history")
            second_result, second_payload = run_scanner(repository, "--scope", "history")

            self.assertEqual(first_result.returncode, 0)
            self.assertEqual(second_result.returncode, 0)
            self.assertEqual(first_payload, second_payload)
            self.assertEqual(first_payload["coverage"]["history_blobs_scanned"], 1)
            self.assertTrue(
                any(record.get("category") == "path-email-address" for record in first_payload["candidates"])
            )

    def test_binary_lfs_and_submodule_surfaces_are_reported_as_gaps(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            initialize_repository(
                repository,
                {
                    "pointer.bin": (
                        "version https://git-lfs.github.com/spec/v1\n"
                        "oid sha256:" + "0" * 64 + "\nsize 42\n"
                    ),
                    "document.pdf": b"%PDF-1.7\nfixture",
                    "image.png": b"\x89PNG\r\n\x1a\nfixture",
                    "records.sqlite": b"SQLite format 3\x00fixture",
                    "binary.dat": b"\x00\x01\x02fixture",
                },
            )
            commit = run_git(repository, "rev-parse", "HEAD").strip()
            run_git(repository, "update-index", "--add", "--cacheinfo", f"160000,{commit},external-module")
            run_git(repository, "commit", "--quiet", "-m", "Add submodule fixture")

            result, payload = run_scanner(repository, "--scope", "full")

            self.assertEqual(result.returncode, 0)
            expected = {
                "git-lfs-pointer-not-inspected",
                "pdf-content-not-inspected",
                "image-content-and-metadata-not-inspected",
                "database-content-not-inspected",
                "binary-content-not-inspected",
                "submodule-content-not-inspected",
            }
            self.assertTrue(expected.issubset(categories(payload, "gaps")))

    def test_removed_historical_symlink_and_submodule_remain_explicit_gaps(self) -> None:
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            initialize_repository(repository)
            token = f"target-{secrets.token_hex(12)}@example.invalid"
            link_blob = run_git(
                repository, "hash-object", "-w", "--stdin", input_text=token + "\n"
            ).strip()
            commit = run_git(repository, "rev-parse", "HEAD").strip()
            run_git(
                repository,
                "update-index",
                "--add",
                "--cacheinfo",
                f"120000,{link_blob},historical-link",
            )
            run_git(
                repository,
                "update-index",
                "--add",
                "--cacheinfo",
                f"160000,{commit},historical-module",
            )
            run_git(repository, "commit", "--quiet", "-m", "Add historical unsupported surfaces")
            run_git(repository, "update-index", "--force-remove", "historical-link", "historical-module")
            run_git(repository, "commit", "--quiet", "-m", "Remove historical unsupported surfaces")

            full_result, full_payload = run_scanner(repository, "--scope", "full")
            path_result, path_payload = run_scanner(
                repository, "--scope", "path", "--path", "historical-link"
            )

            self.assertEqual(full_result.returncode, 0, full_result.stderr)
            self.assertEqual(path_result.returncode, 0, path_result.stderr)
            full_gaps = categories(full_payload, "gaps")
            self.assertIn("historical-symlink-target-not-inspected", full_gaps)
            self.assertIn("historical-submodule-content-not-inspected", full_gaps)
            self.assertIn(
                "historical-symlink-target-not-inspected", categories(path_payload, "gaps")
            )
            self.assertFalse(
                any(
                    record.get("scope") == "history"
                    and record.get("path") == "historical-link"
                    and record.get("category") == "email-address"
                    for record in full_payload["candidates"]
                )
            )
            self.assertNotIn(token, full_result.stdout)
            self.assertNotIn(token, path_result.stdout)

    def test_git_environment_cannot_redirect_scope_or_execute_fsmonitor(self) -> None:
        with temporary_directory() as temporary:
            root = Path(temporary)
            repository = root / "repo"
            hostile = root / "hostile"
            initialize_repository(repository)
            initialize_repository(hostile)
            token = f"hostile-{secrets.token_hex(12)}@example.invalid"
            write_file(hostile, "hostile-record.txt", token + "\n")
            commit_all(hostile, "Add hostile record")
            hook, marker = create_fsmonitor_hook(root)
            run_git(repository, "config", "core.fsmonitor", hook.as_posix())

            inherited = {
                "GIT_DIR": str(hostile / ".git"),
                "GIT_WORK_TREE": str(hostile),
                "GIT_INDEX_FILE": str(hostile / ".git" / "index"),
                "GIT_CONFIG_PARAMETERS": f"'core.fsmonitor={hook.as_posix()}'",
            }
            probe_environment = git_environment()
            probe_environment.update(inherited)
            probe = subprocess.run(
                ["git", "-C", str(repository), "status", "--short"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                env=probe_environment,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertTrue(marker.exists(), "The hostile fsmonitor setup was not exercised.")
            marker.unlink()

            result, payload = run_scanner(
                repository,
                "--scope",
                "full",
                inherited_git_environment=inherited,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(marker.exists())
            self.assertFalse(
                any(record.get("path") == "hostile-record.txt" for record in payload["candidates"])
            )
            self.assertNotIn(token, result.stdout)
            self.assertNotIn(str(hostile), result.stdout)

    def test_documented_scanner_path_exists_and_cli_emits_schema(self) -> None:
        self.assertTrue(SCANNER.is_file())
        with temporary_directory() as temporary:
            repository = Path(temporary) / "repo"
            initialize_repository(repository)
            result, payload = run_scanner(repository, "--scope", "changes")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(payload.get("schema_version"), 1)
            self.assertIsInstance(payload.get("coverage"), dict)
            self.assertIsInstance(payload.get("gaps"), list)


if __name__ == "__main__":
    unittest.main()
