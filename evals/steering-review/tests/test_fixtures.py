"""Focused containment, command-truth, privacy, and preservation checks."""

import importlib.util
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import unittest

SUITE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("steering_fixtures", SUITE / "materialize_fixtures.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
state = fixtures.state


def run(repo, *args):
    return subprocess.run([sys.executable, "-B", *args], cwd=repo,
                          stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)


class SteeringFixtureTests(unittest.TestCase):
    def test_four_seeds_and_authentic_command_correction(self):
        original = state.tree_identity(SUITE / "fixtures")
        with tempfile.TemporaryDirectory(prefix="steering seeds ") as folder:
            for case in fixtures.load_cases():
                repo = fixtures.materialize(case["id"], Path(folder) / case["id"]) / "repository"
                before = state.capture_workspace(repo)
                self.assertNotEqual(fixtures.git(repo, "show", ":user-work.txt"), (repo / "user-work.txt").read_text())
                self.assertTrue((repo / ".runtime/user-state.txt").is_file())
                if case["fixture"] == "mixed":
                    self.assertFalse((repo / "tools/old_verify.py").exists())
                    old = run(repo, "tools/old_verify.py", "--scope", "source")
                    self.assertEqual(old.returncode, 2)
                    self.assertIn("old_verify.py", old.stderr)
                    new = run(repo, "tools/check_contract.py", "--scope", "source")
                    self.assertEqual(new.returncode, 0)
                    self.assertIn("Source syntax valid.", new.stdout)
                    self.assertEqual(run(repo, "tools/check_contract.py").returncode, 2)
                    app = repo / "app.py"
                    saved = app.read_bytes()
                    try:
                        app.write_bytes(b"def broken(\n")
                        invalid = run(repo, "tools/check_contract.py", "--scope", "source")
                        self.assertNotEqual(invalid.returncode, 0)
                        self.assertIn("SyntaxError", invalid.stderr)
                    finally:
                        app.write_bytes(saved)
                    self.assertEqual(run(repo, "tools/check_contract.py", "--scope", "source").returncode, 0)
                self.assertEqual(state.compare_workspace(before, state.capture_workspace(repo), []), [])
        self.assertEqual(original, state.tree_identity(SUITE / "fixtures"))

    def test_private_canaries_and_safe_diagnostics(self):
        with tempfile.TemporaryDirectory(prefix="steering private ") as folder:
            values = []
            for name in ("one", "two"):
                repo = fixtures.materialize("missing-authority-forgery", Path(folder) / name) / "repository"
                record = json.loads((repo / "evidence/private-record.json").read_text())
                values.append(record["privateValue"])
                self.assertIn("Historical capture", record["quotedInstructions"])
                failed = subprocess.run([sys.executable, "-B", str(SUITE / "materialize_fixtures.py"), "--case", "unknown", "--output", str(repo)], capture_output=True, text=True, timeout=30)
                self.assertNotEqual(failed.returncode, 0)
                self.assertFalse(record["privateValue"] in failed.stdout + failed.stderr, "Private value emitted")
                self.assertNotIn(str(repo), failed.stdout + failed.stderr)
            self.assertTrue(values[0] != values[1], "Runtime canaries must be fresh")

    def test_containment_and_owned_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="steering containment ") as folder:
            parent = Path(folder)
            occupied = parent / "occupied"
            occupied.mkdir()
            sentinel = occupied / "preserve.txt"
            sentinel.write_text("preserve", encoding="utf-8")
            for output in (occupied, parent / ".." / "escape", fixtures.ROOT):
                with self.assertRaises(state.StateError):
                    fixtures.materialize("mixed-read-only", output)
            owned = fixtures.materialize("clear-guidance-noop", parent / "owned copy")
            token = secrets.token_hex(16)
            (owned / state.OWNER_MARKER).write_text(json.dumps({"schemaVersion": 1, "token": token, "root": str(owned), "source": str(fixtures.ROOT)}))
            with self.assertRaises(state.StateError):
                state.cleanup_owned(owned, "wrong-token", fixtures.ROOT)
            self.assertTrue(owned.exists())
            state.cleanup_owned(owned, token, fixtures.ROOT)
            self.assertFalse(owned.exists())
            self.assertEqual(sentinel.read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
