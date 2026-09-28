"""Offline state/ownership tests using only disposable local repositories."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals import comparison_state as state


class PathAndOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="p537 comparison state ")
        self.base = Path(self.temporary.name)
        self.source = self.base / "source with spaces"
        self.source.mkdir()
        (self.source / "file.txt").write_bytes(b"preserve original\r\n")

    def tearDown(self):
        self.temporary.cleanup()

    def owned(self):
        root = self.base / "owned bundle"
        root.mkdir()
        marker = {"schemaVersion": 1, "token": "external-test-token",
                  "root": str(root), "source": str(self.source)}
        (root / state.OWNER_MARKER).write_text(json.dumps(marker), encoding="utf-8")
        return root

    def test_complete_copy_includes_hidden_ignored_and_empty_directories(self):
        (self.source / ".git").mkdir()
        (self.source / ".git" / "config").write_bytes(b"synthetic git bytes")
        (self.source / ".gitignore").write_bytes(b"ignored/\n")
        (self.source / "ignored").mkdir()
        (self.source / "ignored" / "payload").write_bytes(b"opaque fixture content")
        (self.source / "empty folder").mkdir()
        destination = self.base / "copy with spaces"
        before = state.tree_identity(self.source)
        state.copy_tree(self.source, destination)
        self.assertEqual(before, state.tree_identity(destination))
        (destination / "file.txt").write_bytes(b"independent copied inode")
        self.assertEqual((self.source / "file.txt").read_bytes(), b"preserve original\r\n")

    def test_plain_packet_snapshot(self):
        captured = state.capture_workspace(self.source)
        self.assertIsNone(captured["git"])
        self.assertEqual([], state.compare_workspace(captured, captured, []))

    def test_malformed_snapshots_are_safe_errors(self):
        before = state.capture_workspace(self.source)
        bad_values = [None, {}, {**before, "files": {"bad": None}},
                      {**before, "schemaVersion": True}]
        for after in bad_values:
            with self.subTest(snapshot_type=type(after).__name__), self.assertRaises(state.StateError) as caught:
                state.compare_workspace(before, after, [])
            self.assertEqual(caught.exception.code, "snapshot-invalid")

    def test_source_overlap_in_both_directions_is_refused(self):
        for output in (self.source, self.source / "child", self.base):
            with self.subTest(output=output.name), self.assertRaises(state.StateError) as caught:
                state.require_external(output, self.source)
            self.assertEqual(caught.exception.code, "source-overlap")

    def test_nonempty_destination_is_preserved(self):
        destination = self.base / "preexisting"
        destination.mkdir()
        (destination / "user.txt").write_bytes(b"existing work")
        with self.assertRaises(state.StateError) as caught:
            state.copy_tree(self.source, destination)
        self.assertEqual(caught.exception.code, "destination-not-empty")
        self.assertEqual((destination / "user.txt").read_bytes(), b"existing work")

    def test_relative_traversal_is_refused_before_resolution(self):
        with self.assertRaises(state.StateError) as caught:
            state.checked_path(self.source / ".." / "source with spaces")
        self.assertEqual(caught.exception.code, "path-invalid")

    def test_missing_path_requires_explicit_allowance(self):
        missing = self.base / "new" / "nested"
        with self.assertRaises(state.StateError):
            state.checked_path(missing)
        self.assertEqual(missing, state.checked_path(missing, must_exist=False))
        self.assertFalse(missing.exists())

    def test_real_link_ancestor_and_leaf_are_refused(self):
        linked = self.base / "linked"
        try:
            linked.symlink_to(self.source, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Host does not permit creation of symbolic links.")
        for selected in (linked, linked / "file.txt", linked / "new.txt"):
            with self.subTest(path=selected.name), self.assertRaises(state.StateError) as caught:
                state.checked_path(selected, must_exist=False)
            self.assertEqual(caught.exception.code, "path-linked")

    def test_reparse_attribute_is_refused_without_link_privileges(self):
        actual_lstat = Path.lstat
        def simulated_lstat(path):
            actual = actual_lstat(path)
            if path == self.source:
                return SimpleNamespace(st_mode=actual.st_mode, st_file_attributes=0x400)
            return actual
        with mock.patch.object(Path, "lstat", simulated_lstat):
            with self.assertRaises(state.StateError) as caught:
                state.checked_path(self.source / "file.txt")
        self.assertEqual(caught.exception.code, "path-linked")

    def test_nonregular_entry_refused(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("Host has no FIFO creation interface.")
        os.mkfifo(self.source / "pipe")
        with self.assertRaises(state.StateError) as caught:
            state.tree_identity(self.source)
        self.assertEqual(caught.exception.code, "entry-unsupported")

    def test_copy_detects_source_drift(self):
        actual_copy = shutil.copy2
        def changing_copy(source, destination, **kwargs):
            result = actual_copy(source, destination, **kwargs)
            Path(source).write_bytes(b"changed during snapshot")
            return result
        with mock.patch.object(shutil, "copy2", changing_copy):
            with self.assertRaises(state.StateError) as caught:
                state.copy_tree(self.source, self.base / "copy")
        self.assertEqual(caught.exception.code, "copy-drift")

    def test_owned_cleanup_removes_only_exact_bundle(self):
        root = self.owned()
        state.copy_tree(self.source, root / "fixture")
        original = state.tree_identity(self.source)
        state.cleanup_owned(root, "external-test-token", self.source)
        self.assertFalse(root.exists())
        self.assertEqual(original, state.tree_identity(self.source))

    def test_wrong_token_and_modified_marker_are_refused(self):
        root = self.owned()
        with self.assertRaises(state.StateError) as caught:
            state.cleanup_owned(root, "foreign-token", self.source)
        self.assertEqual(caught.exception.code, "owner-invalid")
        marker = root / state.OWNER_MARKER
        owner = json.loads(marker.read_text())
        owner["root"] = str(self.base)
        marker.write_text(json.dumps(owner), encoding="utf-8")
        with self.assertRaises(state.StateError) as caught:
            state.cleanup_owned(root, "external-test-token", self.source)
        self.assertEqual(caught.exception.code, "owner-invalid")
        self.assertTrue(root.exists())

    def test_duplicate_marker_keys_are_refused(self):
        root = self.owned()
        marker = root / state.OWNER_MARKER
        text = marker.read_text().replace('"schemaVersion": 1', '"schemaVersion": 1, "schemaVersion": 1')
        marker.write_text(text, encoding="utf-8")
        with self.assertRaises(state.StateError) as caught:
            state.cleanup_owned(root, "external-test-token", self.source)
        self.assertEqual(caught.exception.code, "owner-invalid")

    def test_cleanup_failure_is_reported_and_not_hidden(self):
        root = self.owned()
        with mock.patch.object(shutil, "rmtree", side_effect=PermissionError("private path")):
            with self.assertRaises(state.StateError) as caught:
                state.cleanup_owned(root, "external-test-token", self.source)
        self.assertEqual(caught.exception.code, "cleanup-failed")
        self.assertNotIn("private path", str(caught.exception))
        self.assertTrue(root.exists())

    def test_errors_never_expose_dynamic_diagnostics(self):
        failure = state.StateError("private-canary-value")
        self.assertEqual(failure.code, "workspace-unavailable")
        self.assertNotIn("private", str(failure))


@unittest.skipUnless(shutil.which("git"), "Git is required for disposable fixture checks.")
class WorkspaceStateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="p537 git comparison ")
        self.root = Path(self.temporary.name) / "target with spaces"
        self.root.mkdir()
        self.git("init", "--quiet")
        self.git("config", "user.name", "Synthetic evaluation author")
        self.git("config", "user.email", "synthetic@example.invalid")
        self.git("config", "core.autocrlf", "false")
        (self.root / "README.md").write_bytes(b"Current documentation\n")
        (self.root / "unrelated.txt").write_bytes(b"Original unrelated work\n")
        (self.root / ".gitignore").write_bytes(b"ignored/\n")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "Synthetic initial state")
        (self.root / "unrelated.txt").write_bytes(b"Earlier staged user changes\n")
        self.git("add", "unrelated.txt")
        (self.root / "unrelated.txt").write_bytes(b"Earlier staged user changes\nEarlier unstaged changes\n")
        (self.root / "untracked.txt").write_bytes(b"Earlier untracked work\n")
        (self.root / "ignored").mkdir()
        (self.root / "ignored" / "data.bin").write_bytes(b"Earlier ignored bytes\0\1\2")

    def tearDown(self):
        self.temporary.cleanup()

    def git(self, *arguments):
        result = subprocess.run(
            ["git", "-c", "core.hooksPath=" + os.devnull, *arguments],
            cwd=self.root, env=state._git_environment(), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=30, check=False,
        )
        if result.returncode:
            self.fail("Synthetic fixture Git setup failed.")
        return result.stdout

    def test_capture_is_read_only_with_staged_unstaged_ignored_and_untracked(self):
        original = state.tree_identity(self.root)
        first = state.capture_workspace(self.root)
        second = state.capture_workspace(self.root)
        self.assertEqual(first, second)
        self.assertEqual(original, state.tree_identity(self.root))
        self.assertIn("ignored/data.bin", first["files"])
        self.assertIn("untracked.txt", first["files"])
        self.assertEqual([], state.compare_workspace(first, second, []))

    def test_authorized_file_edit_preserves_dirty_user_state(self):
        before = state.capture_workspace(self.root)
        (self.root / "README.md").write_bytes(b"Updated documentation\n")
        after = state.capture_workspace(self.root)
        self.assertEqual([], state.compare_workspace(before, after, ["README.md"]))
        self.assertIn("unauthorized-file-change", state.compare_workspace(before, after, []))

    def test_file_scope_is_exact_and_directory_scope_is_explicit(self):
        before = state.capture_workspace(self.root)
        (self.root / "README.md.backup").write_bytes(b"not authorized")
        after = state.capture_workspace(self.root)
        self.assertIn("unauthorized-file-change", state.compare_workspace(before, after, ["README.md"]))
        (self.root / "README.md.backup").unlink()
        before = state.capture_workspace(self.root)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "new.md").write_bytes(b"authorized child")
        after = state.capture_workspace(self.root)
        self.assertEqual([], state.compare_workspace(before, after, ["docs/"]))
        self.assertEqual([], state.compare_workspace(before, after, ["docs/new.md"]))
        self.assertIn("unauthorized-file-change", state.compare_workspace(before, after, ["docs"]))

    def test_ignored_and_unrelated_state_changes_are_detected(self):
        before = state.capture_workspace(self.root)
        (self.root / "ignored" / "data.bin").write_bytes(b"unauthorized replacement")
        (self.root / "untracked.txt").unlink()
        after = state.capture_workspace(self.root)
        failures = state.compare_workspace(before, after, ["README.md"])
        self.assertIn("unauthorized-file-change", failures)
        self.assertIn("unrelated-git-status-change", failures)

    def test_staging_authorized_path_is_still_a_preservation_failure(self):
        before = state.capture_workspace(self.root)
        (self.root / "README.md").write_bytes(b"authorized bytes; staging not authorized\n")
        self.git("add", "README.md")
        after = state.capture_workspace(self.root)
        self.assertIn("git-staged-change", state.compare_workspace(before, after, ["README.md"]))

    def test_raw_index_changes_are_diagnostic_not_semantic_failures(self):
        before = state.capture_workspace(self.root)
        after = copy.deepcopy(before)
        after["rawIndexHash"] = "changed-stat-cache-only"
        self.assertEqual([], state.compare_workspace(before, after, []))
        # Real index rewrite without content changes: index version conversion.
        self.git("update-index", "--index-version", "4")
        actual = state.capture_workspace(self.root)
        self.assertNotEqual(before["rawIndexHash"], actual["rawIndexHash"])
        self.assertEqual([], state.compare_workspace(before, actual, []))

    def test_config_refs_and_branch_changes_fail_even_if_files_unchanged(self):
        before = state.capture_workspace(self.root)
        self.git("config", "comparison.synthetic", "changed")
        self.git("branch", "synthetic-extra")
        after = state.capture_workspace(self.root)
        failures = state.compare_workspace(before, after, [])
        self.assertIn("git-config-change", failures)
        self.assertIn("git-refs-change", failures)

    def test_copied_fixture_has_identical_bytes_and_semantic_state(self):
        destination = Path(self.temporary.name) / "second target"
        state.copy_tree(self.root, destination)
        self.assertEqual(state.tree_identity(self.root), state.tree_identity(destination))
        self.assertEqual(state.capture_workspace(self.root), state.capture_workspace(destination))

    def test_inherited_git_injection_and_fsmonitor_are_disabled(self):
        self.git("config", "core.fsmonitor", "must-not-run-synthetic-executable")
        with mock.patch.dict(os.environ, {"GIT_DIR": "invalid inherited path", "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.bare", "GIT_CONFIG_VALUE_0": "true"}):
            captured = state.capture_workspace(self.root)
        self.assertIsNotNone(captured["git"]["head"])

    def test_filters_and_includes_are_rejected_before_worktree_commands(self):
        config = self.root / ".git" / "config"
        original = config.read_bytes()
        snippets = (
            '[filter "synthetic"]\n clean = must-not-run-synthetic-command\n',
            '[filter "synthetic"]\n smudge = must-not-run-synthetic-command\n',
            '[filter "synthetic"]\n process = must-not-run-synthetic-command\n',
            '[include]\n path = missing-synthetic-include\n',
            '[includeIf "gitdir:**/target/**"]\n path = missing-synthetic-include\n',
        )
        for snippet in snippets:
            with self.subTest(kind=snippet.splitlines()[0]):
                config.write_bytes(original + snippet.encode())
                baseline = state.tree_identity(self.root)
                with mock.patch.object(state, "_git", wraps=state._git) as invoked:
                    with self.assertRaises(state.StateError) as caught:
                        state.capture_workspace(self.root)
                self.assertEqual(caught.exception.code, "git-executable-configuration")
                self.assertEqual(invoked.call_count, 1)
                self.assertEqual(invoked.call_args.args[1:],
                                 ("config", "--local", "--no-includes", "--null", "--list"))
                self.assertEqual(state.tree_identity(self.root), baseline)
        config.write_bytes(original)

    def test_per_worktree_filter_configuration_is_also_rejected(self):
        self.git("config", "extensions.worktreeConfig", "true")
        (self.root / ".git" / "config.worktree").write_text(
            '[filter "synthetic"]\n process = must-not-run-synthetic-command\n', encoding="utf-8")
        with mock.patch.object(state, "_git", wraps=state._git) as invoked:
            with self.assertRaises(state.StateError) as caught:
                state.capture_workspace(self.root)
        self.assertEqual(caught.exception.code, "git-executable-configuration")
        self.assertEqual(invoked.call_count, 2)
        self.assertTrue(all(call.args[1] == "config" and "--no-includes" in call.args
                            for call in invoked.call_args_list))

    def test_filter_metadata_without_executable_commands_remains_supported(self):
        self.git("config", "filter.synthetic.required", "false")
        captured = state.capture_workspace(self.root)
        self.assertIsNotNone(captured["git"]["head"])

    def test_scope_traversal_and_git_permissions_are_rejected(self):
        before = state.capture_workspace(self.root)
        for path in ("../README.md", "/README.md", "C:/README.md", ".git/", "docs/../README.md", "docs\\readme.md", "docs//readme.md", "README.md:stream"):
            with self.subTest(path=path), self.assertRaises(state.StateError) as caught:
                state.compare_workspace(before, before, [path])
            self.assertEqual(caught.exception.code, "scope-invalid")

    def test_linked_git_layout_is_rejected(self):
        (self.root / ".git" / "commondir").write_text("../other-git", encoding="utf-8")
        with self.assertRaises(state.StateError) as caught:
            state.capture_workspace(self.root)
        self.assertEqual(caught.exception.code, "git-layout")

    def test_git_errors_are_redacted(self):
        with mock.patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=2, stdout=b"private content", stderr=b"private path")):
            with self.assertRaises(state.StateError) as caught:
                state.capture_workspace(self.root)
        self.assertEqual(caught.exception.code, "git-command")
        self.assertNotIn("private", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
