"""Focused fixture authenticity, preservation, and containment checks."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SUITE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("harness_fixtures", SUITE / "materialize_fixtures.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
state = fixtures.state


def run(repo, *args):
    return subprocess.run([sys.executable, "-B", *args], cwd=repo,
                          stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)


class HarnessFixtureTests(unittest.TestCase):
    def test_four_seeds_preserve_dirty_state(self):
        original = state.tree_identity(SUITE / "fixtures")
        with tempfile.TemporaryDirectory(prefix="harness seeds ") as folder:
            for case in fixtures.load_cases():
                repo = fixtures.materialize(case["id"], Path(folder) / case["id"]) / "repository"
                before = state.capture_workspace(repo)
                if case["id"] == "missing-persistence-harness":
                    self.assertFalse((repo / "verify_contract.py").exists())
                else:
                    args = {"counter": ["verify_contract.py"], "records": ["-m", "unittest", "discover", "-s", "tests"], "browser": ["api_check.py"]}[case["fixture"]]
                    self.assertEqual(run(repo, *args).returncode, 0)
                self.assertNotEqual(fixtures.git(repo, "show", ":user-work.txt"), (repo / "user-work.txt").read_text())
                self.assertTrue((repo / ".runtime/user-state.txt").is_file())
                self.assertEqual(state.compare_workspace(before, state.capture_workspace(repo), []), [])
        self.assertEqual(original, state.tree_identity(SUITE / "fixtures"))

    def test_fault_detection_and_restoration(self):
        with tempfile.TemporaryDirectory(prefix="harness faults ") as folder:
            for case, name, old, new, args in [
                ("adequate-existing-verification", "counter.py", b'path.write_text(json.dumps({"value": value}) + "\\n", encoding="utf-8")', b'path.write_text(json.dumps({"value": 0}) + "\\n", encoding="utf-8")', ["verify_contract.py"]),
                ("ineffective-passing-test", "records.py", b"line.strip() for line", b"'wrong' for line", ["-m", "unittest", "discover", "-s", "tests"]),
            ]:
                repo = fixtures.materialize(case, Path(folder) / case) / "repository"
                before = state.capture_workspace(repo)
                source = repo / name
                original = source.read_bytes()
                self.assertIn(old, original)
                self.assertEqual(run(repo, *args).returncode, 0)
                try:
                    source.write_bytes(original.replace(old, new))
                    observed = run(repo, *args)
                    if name == "records.py":
                        self.assertEqual(observed.returncode, 0)  # Existing weak assertion misses the fault.
                        observed = run(repo, "-c", "from records import parse_records; assert parse_records(' alpha \\n\\n beta') == ['alpha', 'beta']")
                    self.assertNotEqual(observed.returncode, 0)
                    self.assertIn("AssertionError", observed.stderr)
                    if name == "counter.py":
                        self.assertIn("persisted value mismatch", observed.stderr)
                finally:
                    source.write_bytes(original)
                self.assertEqual(run(repo, *args).returncode, 0)
                self.assertEqual(state.compare_workspace(before, state.capture_workspace(repo), []), [])

    def test_unsafe_destinations_preserve_existing_files(self):
        with tempfile.TemporaryDirectory(prefix="harness containment ") as folder:
            occupied = Path(folder) / "occupied"
            occupied.mkdir()
            marker = occupied / "keep.txt"
            marker.write_text("keep", encoding="utf-8")
            for destination in (occupied, Path(folder) / ".." / "escape", fixtures.ROOT):
                with self.assertRaises(state.StateError):
                    fixtures.materialize("missing-persistence-harness", destination)
            with self.assertRaises(fixtures.FixtureError):
                fixtures.materialize("../unknown", Path(folder) / "unused")
            self.assertEqual(marker.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
