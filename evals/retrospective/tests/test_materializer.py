"""Verify fixture boundaries and actual Git state, not retrospective prose."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location("retrospective_fixtures", ROOT / "evals/retrospective/materialize_fixtures.py")
fixture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fixture)


class MaterializerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="retrospective test spaces ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cases = fixture.load_cases()

    def test_all_cases_are_separate_and_clean_except_declared_dirty_state(self):
        source_before = fixture.state.tree_identity(fixture.FIXTURES)
        outputs = fixture.materialize_selected(self.cases, self.root / "all cases")
        self.assertEqual(len(outputs), len(self.cases))
        for case, output in zip(self.cases, outputs):
            self.assertEqual(list((output / "task-temporary").iterdir()), [])
            self.assertTrue((output / "supplied-evidence/observations.md").is_file())
            snapshot = fixture.state.capture_workspace(output / "repository")
            status = fixture.git(output / "repository", "status", "--porcelain")
            if case["git"]["mode"] == "clean":
                self.assertEqual(status, "")
            else:
                self.assertIn("MM project.py", status)
                self.assertIn("?? untracked-user.txt", status)
                self.assertEqual(fixture.git(output / "repository", "show", ":project.py"), "SCHEMA_VERSION = 3\n")
                self.assertEqual((output / "repository/project.py").read_text(), "SCHEMA_VERSION = 4\n")
                self.assertTrue((output / "repository/ignored-user.txt").is_file())
            self.assertEqual(fixture.state.compare_workspace(snapshot, fixture.state.capture_workspace(output / "repository"), []), [])
        self.assertEqual(fixture.state.tree_identity(fixture.FIXTURES), source_before)

    def test_copying_and_removing_task_work_preserves_originals_and_staging(self):
        case = next(c for c in self.cases if c["git"]["mode"] == "dirty")
        output = fixture.materialize_selected([case], self.root / "one")[0]
        original = fixture.state.tree_identity(output / "supplied-evidence")
        repository = fixture.state.capture_workspace(output / "repository")
        copy = output / "task-temporary/worksheet.md"
        copy.write_text("Sanitized abstract observation only.\n")
        copy.unlink()
        self.assertEqual(fixture.state.tree_identity(output / "supplied-evidence"), original)
        self.assertEqual(fixture.state.compare_workspace(repository, fixture.state.capture_workspace(output / "repository"), []), [])
        self.assertEqual(list((output / "task-temporary").iterdir()), [])

    def test_unsafe_destinations_leave_existing_content_unchanged(self):
        occupied = self.root / "occupied"
        occupied.mkdir()
        sentinel = occupied / "keep.txt"
        sentinel.write_text("User content")
        for dest in (occupied, ROOT / "must-not-create", self.root / "a/../b"):
            with self.assertRaises(fixture.state.StateError):
                fixture.materialize_selected(self.cases[:1], dest)
        self.assertEqual(sentinel.read_text(), "User content")

    def test_linked_destination_is_rejected(self):
        target = self.root / "real"
        target.mkdir()
        link = self.root / "link"
        try:
            link.symlink_to(target, target_is_directory=True)
        except OSError:
            self.skipTest("Host cannot create physical symlinks")
        with self.assertRaises(fixture.state.StateError):
            fixture.materialize_selected(self.cases[:1], link / "output")
        self.assertEqual(list(target.iterdir()), [])

    def test_invalid_manifest_and_cli_diagnostics_do_not_echo_input(self):
        manifest = json.loads(fixture.MANIFEST.read_text())
        manifest["cases"][0]["fixture"] = "../PRIVATE_INPUT_CANARY"
        with mock.patch.object(fixture.json, "loads", return_value=manifest):
            with self.assertRaises(fixture.FixtureError) as caught:
                fixture.load_cases()
        self.assertNotIn("PRIVATE_INPUT_CANARY", str(caught.exception))
        result = subprocess.run([sys.executable, "-B", str(fixture.SUITE / "materialize_fixtures.py"), "--case", "PRIVATE_INPUT_CANARY", "--output", str(self.root / "unused")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("PRIVATE_INPUT_CANARY", result.stdout + result.stderr)
        self.assertFalse((self.root / "unused").exists())

    def test_disclosure_canaries_are_local_and_unique(self):
        case = next(c for c in self.cases if c["git"]["mode"] == "dirty")
        outputs = [fixture.materialize_selected([case], self.root / name)[0] for name in ("first", "second")]
        values = [(path / "supplied-evidence/private-source.txt").read_text().splitlines()[0] for path in outputs]
        self.assertTrue(values[0] != values[1], "Runtime canary was reused")
        self.assertTrue(all("PRIVATE_" in value for value in values))


if __name__ == "__main__":
    unittest.main()
