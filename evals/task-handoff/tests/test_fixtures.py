"""Focused offline checks for the two checkpoint smoke seeds."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

SUITE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("handoff_fixtures", SUITE / "materialize_fixtures.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
state = fixtures.state


class CheckpointFixtureTests(unittest.TestCase):
    def test_two_seeds_preserve_dirty_state_and_source(self):
        original = state.tree_identity(SUITE / "fixtures")
        with tempfile.TemporaryDirectory(prefix="handoff fixture checks ") as folder:
            snapshots = []
            for case_id in ("approved-persistence", "conversation-only-capture"):
                target = fixtures.materialize(case_id, Path(folder) / case_id)
                repo = target / "repository"
                before = state.capture_workspace(repo)
                self.assertNotEqual(fixtures.git(repo, "show", ":user-work.txt"), (repo / "user-work.txt").read_text())
                self.assertTrue((repo / "untracked-user.txt").is_file())
                self.assertTrue((repo / "ignored-user.txt").is_file())
                self.assertFalse((repo / "handoff.md").exists())
                self.assertEqual(state.compare_workspace(before, state.capture_workspace(repo), []), [])
                snapshots.append(before)
            # Separate preparation has different index stat caches; compare
            # staged semantics and file bytes, not those incidental timestamps.
            self.assertEqual(state.compare_workspace(snapshots[0], snapshots[1], []), [])
        self.assertEqual(original, state.tree_identity(SUITE / "fixtures"))

    def test_changed_worktree_with_unchanged_head_is_visible(self):
        with tempfile.TemporaryDirectory(prefix="handoff drift ") as folder:
            repo = fixtures.materialize("conversation-only-capture", Path(folder) / "seed") / "repository"
            before = state.capture_workspace(repo)
            head = fixtures.git(repo, "rev-parse", "HEAD")
            staged = fixtures.git(repo, "diff", "--cached", "--binary")
            (repo / "quantity.py").write_text("def accepted(quantity):\n    return quantity >= 0\n", encoding="utf-8")
            self.assertEqual(head, fixtures.git(repo, "rev-parse", "HEAD"))
            self.assertEqual(staged, fixtures.git(repo, "diff", "--cached", "--binary"))
            after = state.capture_workspace(repo)
            self.assertTrue(state.compare_workspace(before, after, []))
            self.assertEqual(state.compare_workspace(before, after, ["quantity.py"]), [])

    def test_invalid_destinations_preserve_existing_content(self):
        with tempfile.TemporaryDirectory(prefix="handoff containment ") as folder:
            target = Path(folder) / "occupied"
            target.mkdir()
            original = target / "keep.txt"
            original.write_text("keep", encoding="utf-8")
            for destination in (target, Path(folder) / ".." / "escape", fixtures.ROOT):
                with self.assertRaises(state.StateError):
                    fixtures.materialize("approved-persistence", destination)
            self.assertEqual(original.read_text(), "keep")
            with self.assertRaises(fixtures.FixtureError):
                fixtures.materialize("../unknown", Path(folder) / "unused")


if __name__ == "__main__":
    unittest.main()
