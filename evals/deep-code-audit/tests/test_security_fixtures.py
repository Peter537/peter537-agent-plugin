"""Focused preparation and replay checks; never launches an evaluated agent."""
import importlib.util
import json
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import unittest

SUITE = Path(__file__).resolve().parents[1]
ROOT = SUITE.parents[1]
sys.path.insert(0, str(ROOT))
from evals import comparison_state as state

spec = importlib.util.spec_from_file_location("security_fixtures", SUITE / "materialize_fixtures.py")
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)

SELECTED = (
    "web-role-revocation", "web-repeat-state-change", "web-shared-state-isolation",
    "web-record-policy", "web-input-session-upload", "web-upload-boundary-control",
    "web-managed-safe", "non-web-security-control",
)
PROBES = {
    "web-role-revocation": "test_roles",
    "web-repeat-state-change": "test_inventory",
    "web-shared-state-isolation": "test_cache",
    "web-record-policy": "test_projects",
    "web-input-session-upload": "test_upload",
    "web-upload-boundary-control": "test_ingest",
}


def prepare(case_id, output):
    """Wrap the existing materializer with shared external-path checks."""
    destination = state.require_external(output, ROOT)
    if case_id not in SELECTED:
        raise ValueError("Unselected security case")
    case = next(c for c in fixtures.load_manifest()["cases"] if c["id"] == case_id)
    destination.mkdir(parents=True, exist_ok=True)
    repo = fixtures.materialize_case(case, destination)
    (repo / ".gitignore").write_bytes(b"ignored-user.txt\n.runtime/\n")
    (repo / "user-work.txt").write_bytes(b"Original unrelated note.\n")
    fixtures.commit_all(repo, "Synthetic preservation state")
    (repo / "user-work.txt").write_bytes(b"Staged unrelated note.\n")
    fixtures.run_git(repo, "add", "--", "user-work.txt")
    (repo / "user-work.txt").write_bytes(b"Staged unrelated note with an unstaged draft.\n")
    (repo / "untracked-user.txt").write_bytes(b"Preserve this unrelated draft.\n")
    (repo / "ignored-user.txt").write_bytes(b"Preserve ignored content.\n")
    (repo / ".runtime").mkdir()
    (repo / ".runtime/user-state.txt").write_bytes(b"Existing user state.\n")
    return repo


def replay(repo, case_id):
    if case_id in PROBES:
        args = ["-m", "unittest", "-v", PROBES[case_id]]
    elif case_id == "web-managed-safe":
        args = ["-c", "from projects import list_projects; p={'id':'alice','tenant_id':'a'}; rows=[{'id':1,'owner_id':'alice','tenant_id':'a','name':'Own','internal':'hidden'},{'id':2,'owner_id':'bob','tenant_id':'a','name':'Peer'},{'id':3,'owner_id':'alice','tenant_id':'b','name':'Other'}]; assert list_projects(p,rows)==[{'id':1,'name':'Own'}]; print('Owner, tenant and response controls observed')"]
    elif case_id == "non-web-security-control":
        args = ["-c", "from ranges import clamp; assert [clamp(x,0,10) for x in (-1,4,11)]==[0,4,10]; print('Local range behavior observed')"]
    else:
        raise ValueError("Unselected security case")
    return subprocess.run([sys.executable, "-B", *args], cwd=repo, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=30)


class SecurityFixtureTests(unittest.TestCase):
    def test_selected_probes_and_dirty_state_preservation(self):
        original = state.tree_identity(SUITE / "fixtures")
        with tempfile.TemporaryDirectory(prefix="security fixture checks ") as temp:
            for case_id in SELECTED:
                with self.subTest(case=case_id):
                    repo = prepare(case_id, Path(temp) / case_id)
                    before = state.capture_workspace(repo)
                    self.assertTrue(any(row["index"] == "M" and row["worktree"] == "M" for row in before["git"]["status"]))
                    result = replay(repo, case_id)
                    self.assertEqual(result.returncode, 0, "Selected synthetic probe failed; inspect locally")
                    self.assertEqual(state.compare_workspace(before, state.capture_workspace(repo), []), [])
                    self.assertFalse((repo / "uploads").exists())
        self.assertEqual(original, state.tree_identity(SUITE / "fixtures"))

    def test_reject_nonempty_traversal_and_source_overlap(self):
        with tempfile.TemporaryDirectory(prefix="security containment ") as temp:
            parent = Path(temp)
            occupied = parent / "occupied"
            occupied.mkdir()
            sentinel = occupied / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            for output in (occupied, parent / ".." / "escape", ROOT):
                with self.assertRaises(state.StateError):
                    prepare(SELECTED[0], output)
            self.assertEqual(sentinel.read_text(), "keep")

    def test_link_rejection_and_owned_cleanup(self):
        with tempfile.TemporaryDirectory(prefix="security cleanup ") as temp:
            parent = Path(temp)
            source = parent / "source"
            source.mkdir()
            (source / "keep.txt").write_text("keep", encoding="utf-8")
            link = parent / "link"
            try:
                link.symlink_to(source, target_is_directory=True)
            except OSError:
                # Windows may lack symlink privilege; the shared path helper's
                # link check remains in use, without claiming exercised support.
                pass
            else:
                with self.assertRaises(state.StateError):
                    state.require_external(link / "new", ROOT)
                link.unlink()
            owned = parent / "owned"
            prepare(SELECTED[0], owned)
            token = secrets.token_hex(16)
            (owned / state.OWNER_MARKER).write_text(json.dumps({"schemaVersion": 1, "token": token, "root": str(owned), "source": str(ROOT)}))
            with self.assertRaises(state.StateError):
                state.cleanup_owned(owned, "wrong-token", ROOT)
            state.cleanup_owned(owned, token, ROOT)
            self.assertFalse(owned.exists())
            self.assertEqual((source / "keep.txt").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
