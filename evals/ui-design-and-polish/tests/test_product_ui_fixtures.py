"""Focused fixture preparation checks; browser evidence is collected separately."""
import importlib.util
import json
from html.parser import HTMLParser
from pathlib import Path
import secrets
import sys
import tempfile
import unittest

SUITE = Path(__file__).resolve().parents[1]
ROOT = SUITE.parents[1]
sys.path.insert(0, str(ROOT))
from evals import comparison_state as state

spec = importlib.util.spec_from_file_location("product_ui_fixtures", SUITE / "materialize_fixtures.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
SELECTED = ("operational-table-refine", "justified-cards-refine", "generic-workflow-refine", "permission-state-refine")


class Resources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paths = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "script" and "src" in values:
            self.paths.append(values["src"])
        if tag == "link" and values.get("rel") == "stylesheet":
            self.paths.append(values["href"])


def inspect_resources(repo):
    """Check resource closure, not visual quality or executable behavior."""
    parser = Resources()
    parser.feed((repo / "index.html").read_text(encoding="utf-8"))
    for value in parser.paths:
        relative = Path(value)
        if ":" in value or relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Fixture resource must remain local")
        if not state.checked_path(repo / relative).is_file():
            raise ValueError("Fixture resource is missing")
    return parser.paths


def prepare(case_id, output):
    destination = state.require_external(output, ROOT)
    if case_id not in SELECTED:
        raise ValueError("Unselected UI case")
    case = next(c for c in fixtures.load_manifest()["cases"] if c["id"] == case_id)
    destination.mkdir(parents=True, exist_ok=True)
    repo = fixtures.materialize_case(case, destination)
    (repo / ".gitignore").write_bytes(b"ignored-user.txt\n.runtime/\n")
    (repo / "user-work.txt").write_bytes(b"Original unrelated work.\n")
    fixtures.run_git(repo, "add", "--all")
    fixtures.run_git(repo, "commit", "--quiet", "-m", "Synthetic preservation state")
    (repo / "user-work.txt").write_bytes(b"Staged unrelated work.\n")
    fixtures.run_git(repo, "add", "--", "user-work.txt")
    (repo / "user-work.txt").write_bytes(b"Staged unrelated work plus an unstaged draft.\n")
    (repo / "untracked-user.txt").write_bytes(b"Preserve this draft.\n")
    (repo / "ignored-user.txt").write_bytes(b"Preserve ignored work.\n")
    (repo / ".runtime").mkdir()
    (repo / ".runtime/user-state.txt").write_bytes(b"Existing state.\n")
    return repo


class ProductUiFixtureTests(unittest.TestCase):
    def test_selected_materializations_resources_and_preservation(self):
        original = state.tree_identity(SUITE / "fixtures")
        with tempfile.TemporaryDirectory(prefix="product ui fixtures ") as temp:
            for case_id in SELECTED:
                with self.subTest(case=case_id):
                    repo = prepare(case_id, Path(temp) / case_id)
                    before = state.capture_workspace(repo)
                    self.assertTrue(any(row["index"] == "M" and row["worktree"] == "M" for row in before["git"]["status"]))
                    self.assertIn("styles.css", inspect_resources(repo))
                    self.assertEqual(state.compare_workspace(before, state.capture_workspace(repo), []), [])
        self.assertEqual(original, state.tree_identity(SUITE / "fixtures"))

    def test_unsafe_destinations_and_missing_resource(self):
        with tempfile.TemporaryDirectory(prefix="product ui containment ") as temp:
            parent = Path(temp)
            occupied = parent / "occupied"
            occupied.mkdir()
            (occupied / "keep.txt").write_text("keep")
            for output in (occupied, parent / ".." / "escape", ROOT):
                with self.assertRaises(state.StateError):
                    prepare(SELECTED[0], output)
            self.assertEqual((occupied / "keep.txt").read_text(), "keep")
            (occupied / "index.html").write_text('<link rel="stylesheet" href="missing.css">')
            with self.assertRaises(state.StateError):
                inspect_resources(occupied)
            (occupied / "index.html").write_text('<script src="../keep.js"></script>')
            with self.assertRaises(ValueError):
                inspect_resources(occupied)

    def test_owned_cleanup_preserves_outside_state(self):
        with tempfile.TemporaryDirectory(prefix="product ui cleanup ") as temp:
            parent = Path(temp)
            sentinel = parent / "keep.txt"
            sentinel.write_text("keep")
            owned = parent / "owned"
            prepare(SELECTED[0], owned)
            token = secrets.token_hex(16)
            (owned / state.OWNER_MARKER).write_text(json.dumps({"schemaVersion": 1, "token": token, "root": str(owned), "source": str(ROOT)}))
            with self.assertRaises(state.StateError):
                state.cleanup_owned(owned, "wrong-token", ROOT)
            state.cleanup_owned(owned, token, ROOT)
            self.assertFalse(owned.exists())
            self.assertEqual(sentinel.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
