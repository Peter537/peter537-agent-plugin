"""Focused preparation checks and an authentic surviving-assertion control."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SUITE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("test_value_fixtures", SUITE / "materialize_fixtures.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
state = fixtures.state


def check(repo):
    return subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"],
                          cwd=repo, capture_output=True, text=True, timeout=30)


class TestValueFixtureTests(unittest.TestCase):
    def test_four_seeds_preserve_source_and_dirty_state(self):
        original = state.tree_identity(SUITE / "fixtures")
        with tempfile.TemporaryDirectory(prefix="test value seeds ") as folder:
            for case in fixtures.load_cases():
                repo = fixtures.materialize(case["id"], Path(folder) / case["id"]) / "repository"
                before = state.capture_workspace(repo)
                result = check(repo)
                self.assertEqual(result.returncode, 1 if case["id"] == "failing-test-missing-evidence" else 0)
                if result.returncode:
                    self.assertIn("quantity=0", result.stderr)
                self.assertNotEqual(fixtures.git(repo, "show", ":user-work.txt"), (repo / "user-work.txt").read_text())
                self.assertTrue((repo / "untracked-user.txt").is_file())
                self.assertTrue((repo / "ignored-user.txt").is_file())
                self.assertEqual(state.compare_workspace(before, state.capture_workspace(repo), []), [])
        self.assertEqual(original, state.tree_identity(SUITE / "fixtures"))

    def test_real_survivor_catches_fault_after_consolidation(self):
        with tempfile.TemporaryDirectory(prefix="test value survivor ") as folder:
            repo = fixtures.materialize("authorized-consolidation", Path(folder) / "seed") / "repository"
            before = state.capture_workspace(repo)
            removed = {name: (repo / name).read_bytes() for name in ("tests/test_examples.py", "tests/test_acceptance.py")}
            app = repo / "app.py"
            original = app.read_bytes()
            try:
                for name in removed:
                    (repo / name).unlink()
                self.assertEqual(check(repo).returncode, 0)
                app.write_bytes(original.replace(b"quantity >= 0", b"quantity > 0"))
                result = check(repo)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("test_quantity", result.stderr)
                self.assertIn("quantity=0", result.stderr)
                app.write_bytes(original)
                self.assertEqual(check(repo).returncode, 0)
            finally:
                app.write_bytes(original)
                for name, content in removed.items():
                    (repo / name).write_bytes(content)
            self.assertEqual(state.compare_workspace(before, state.capture_workspace(repo), []), [])

    def test_invalid_destinations_do_not_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="test value containment ") as folder:
            occupied = Path(folder) / "occupied"
            occupied.mkdir()
            marker = occupied / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            for destination in (occupied, Path(folder) / ".." / "escape", fixtures.ROOT):
                with self.assertRaises(state.StateError):
                    fixtures.materialize("mixed-read-only", destination)
            self.assertEqual(marker.read_text(), "keep")
            with self.assertRaises(fixtures.FixtureError):
                fixtures.materialize("../unknown", Path(folder) / "unused")


if __name__ == "__main__":
    unittest.main()
