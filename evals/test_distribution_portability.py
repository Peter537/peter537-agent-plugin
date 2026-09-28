"""Offline package-copy checks; real installation and model trials are separate.

No installer, model, service, or network operation belongs in this module.
The existing prose checker controls are reused rather than reimplemented.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals import comparison_state as state
from evals import run_offline_checks as offline


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_OWNERS = {
    "check_prose_fidelity.py": "write-clearly",
    "inventory_dependency_files.py": "audit-dependencies",
    "scan_repository_data_exposure.py": "audit-data-exposure",
}


def packages(root: Path) -> list[Path]:
    return sorted(path for path in (root / "skills").iterdir()
                  if (path / "SKILL.md").is_file())


def validate_resources(package: Path) -> None:
    """Apply the existing bounded link check with this package as the root."""
    state.tree_identity(package)
    for path in package.rglob("*.md"):
        offline.validate_markdown_file(package, path.relative_to(package).as_posix(), path)
    metadata = package / "agents/openai.yaml"
    if metadata.is_file():
        data = offline.parse_bounded_yaml(metadata.read_text(encoding="utf-8"))
        for key in ("icon_small", "icon_large"):
            value = data.get("interface", {}).get(key)
            if value is not None:
                offline.resolve_repository_path(package, value)


def bundle_members(root: Path) -> dict[str, bytes]:
    """The existing skills-only submission allowlist, never a release upload."""
    members = {}
    paths = [root / ".codex-plugin/plugin.json", root / "assets/logo.png"]
    for package in packages(root):
        for relative, identity in state.tree_identity(package).items():
            if identity["kind"] == "file":
                paths.append(package / relative)
    for path in paths:
        members[path.relative_to(root).as_posix()] = state.checked_path(path).read_bytes()
    return members


def make_package_copy(root: Path, destination: Path, form: str, slug: str) -> Path:
    """Build only reviewed fixture forms, not a general archive extractor."""
    state.require_external(destination, root)
    if form == "individual":
        state.copy_tree(root / "skills" / slug, destination)
        return destination
    destination.mkdir()
    if form == "complete":
        for name in ("skills", ".codex-plugin", ".agents/plugins", "assets"):
            state.copy_tree(root / name, destination / name)
        for name in ("plugin.json", "mcp.json"):
            shutil.copy2(root / name, destination / name)
    elif form == "skills-only":
        members = bundle_members(root)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in sorted(members.items()):
                archive.writestr(name, content)
        buffer.seek(0)
        with zipfile.ZipFile(buffer) as archive:
            if archive.testzip() is not None or set(archive.namelist()) != set(members):
                raise AssertionError("Fixture archive failed integrity or membership checks")
            # Write known allowlisted members individually; never trust arbitrary
            # archive names or call extractall on an externally supplied archive.
            for name, content in members.items():
                if archive.read(name) != content:
                    raise AssertionError("Fixture archive byte mismatch")
                target = state.checked_path(destination / name, must_exist=False)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
    else:
        raise ValueError("Unknown fixture distribution form")
    return destination / "skills" / slug


class DistributionPortabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="distribution portability ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        state.require_external(self.root, ROOT)
        self.original_popen = subprocess.Popen
        patcher = mock.patch.object(subprocess, "Popen", side_effect=self.offline_spawn)
        patcher.start()
        self.addCleanup(patcher.stop)

    def offline_spawn(self, args, *positional, **keywords):
        """A launch canary around every child this maintenance suite starts."""
        if not isinstance(args, (list, tuple)) or not args or keywords.get("shell"):
            raise AssertionError("Unreviewed child launch blocked")
        program = str(args[0])
        if program == "git":
            return self.original_popen(args, *positional, **keywords)
        if (program == sys.executable and len(args) >= 3 and args[1] == "-B"
                and Path(args[2]).name in SCRIPT_OWNERS):
            script = state.checked_path(Path(args[2]))
            source = ROOT / "skills" / SCRIPT_OWNERS[script.name] / "scripts" / script.name
            if script.read_bytes() == source.read_bytes():
                return self.original_popen(args, *positional, **keywords)
        raise AssertionError("Installer, model, service, or unreviewed child launch blocked")

    def git(self, repository: Path, *args: str) -> str:
        env = state._git_environment()
        env.update({"GIT_AUTHOR_NAME": "Portability Fixture", "GIT_COMMITTER_NAME": "Portability Fixture",
                    "GIT_AUTHOR_EMAIL": "fixture@example.invalid", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"})
        result = subprocess.run(["git", "-c", "commit.gpgSign=false", "-c", "core.autocrlf=false",
                                 "-c", f"core.hooksPath={os.devnull}", *args], cwd=repository,
                                env=env, stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, "Fixture Git operation failed; child output suppressed")
        return result.stdout

    def repository(self) -> Path:
        target = self.root / "target repository"
        target.mkdir()
        self.git(target, "init", "--quiet", "--template=")
        (target / "README.md").write_text("Fixture\n", encoding="utf-8")
        (target / ".gitignore").write_text("ignored notes.txt\n", encoding="utf-8")
        self.git(target, "add", ".")
        self.git(target, "commit", "--quiet", "-m", "Fixture")
        (target / "README.md").write_text("Staged user work\n", encoding="utf-8")
        self.git(target, "add", "README.md")
        (target / "README.md").write_text("Staged and unstaged user work\n", encoding="utf-8")
        for name in ("untracked notes.txt", "ignored notes.txt"):
            (target / name).write_text("Unrelated work\n", encoding="utf-8")
        return target

    def script(self, package: Path, name: str, target: Path, *args: str):
        source_state = state.tree_identity(package)
        before = state.capture_workspace(target)
        result = subprocess.run([sys.executable, "-B", str(package / "scripts" / name), *args],
                                cwd=target, env=state._git_environment(), stdin=subprocess.DEVNULL,
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertFalse(state.compare_workspace(before, state.capture_workspace(target), []),
                         "Installed script changed target state")
        self.assertTrue(source_state == state.tree_identity(package), "Installed package changed")
        self.assertFalse((target / "skills").exists())
        return result

    def test_individual_packages_resolve_without_repository_or_siblings(self):
        discovered = packages(ROOT)
        self.assertTrue(discovered)
        for source in discovered:
            with self.subTest(skill=source.name):
                before = state.tree_identity(source)
                copied = make_package_copy(ROOT, self.root / source.name, "individual", source.name)
                self.assertTrue(before == state.tree_identity(copied), "Package byte mismatch")
                validate_resources(copied)
                self.assertTrue(before == state.tree_identity(source), "Source package changed")

    def test_complete_and_skills_only_contents_and_resource_parity(self):
        for form in ("complete", "skills-only"):
            with self.subTest(form=form):
                destination = self.root / form
                make_package_copy(ROOT, destination, form, "write-clearly")
                self.assertEqual({p.name for p in packages(destination)}, {p.name for p in packages(ROOT)})
                self.assertEqual((destination / "assets/logo.png").read_bytes(), (ROOT / "assets/logo.png").read_bytes())
                for source in packages(ROOT):
                    copied = destination / "skills" / source.name
                    self.assertTrue(state.tree_identity(source) == state.tree_identity(copied), "Package byte mismatch")
                    validate_resources(copied)
                if form == "complete":
                    self.assertEqual((destination / "mcp.json").read_bytes(), (ROOT / "mcp.json").read_bytes())
                    self.assertTrue((destination / ".agents/plugins/marketplace.json").is_file())
                else:
                    self.assertEqual({p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()},
                                     set(bundle_members(ROOT)))
                    for name in ("mcp.json", "plugin.json", ".agents", "evals", "TODO.md"):
                        self.assertFalse((destination / name).exists())

    def test_existing_clean_and_dirty_checker_controls_in_each_form(self):
        path = ROOT / "evals/write-clearly/tests/test_check_prose_fidelity.py"
        spec = importlib.util.spec_from_file_location("portability_prose_controls", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for form in ("individual", "complete", "skills-only"):
            package = make_package_copy(ROOT, self.root / form, form, "write-clearly")
            before = state.tree_identity(package)
            for name in ("test_installed_checker_git_mode_from_separate_repository",
                         "test_preexisting_dirty_work_requires_pair_baseline"):
                with self.subTest(form=form, control=name):
                    case = module.FidelityCheckerTests(name)
                    case.install_checker = lambda: package / "scripts/check_prose_fidelity.py"
                    result = unittest.TestResult()
                    case.run(result)
                    self.assertTrue(result.wasSuccessful(), "Existing prose control failed; private output suppressed")
            self.assertTrue(before == state.tree_identity(package), "Installed package changed")

    def test_installed_inventory_uses_target_and_preserves_dirty_state(self):
        target = self.repository()
        (target / "package.json").write_text('{"name":"fixture","dependencies":{"example":"1.0.0"}}\n', encoding="utf-8")
        for form in ("individual", "complete", "skills-only"):
            with self.subTest(form=form):
                package = make_package_copy(ROOT, self.root / form, form, "audit-dependencies")
                result = self.script(package, "inventory_dependency_files.py", target, str(target), "--format", "json")
                self.assertEqual(result.returncode, 0, "Installed inventory failed; child output suppressed")
                payload = json.loads(result.stdout)
                self.assertTrue(any(item["path"] == "package.json" for item in payload["items"]))
                self.assertFalse(any("skills/" in item["path"] for item in payload["items"]))

    def test_installed_scanner_finds_and_redacts_target_evidence(self):
        target = self.repository()
        canary = "record-" + secrets.token_hex(12) + "@example.invalid"
        (target / "diagnostic sample.txt").write_text(canary + "\n", encoding="utf-8")
        for form in ("individual", "complete", "skills-only"):
            with self.subTest(form=form):
                package = make_package_copy(ROOT, self.root / form, form, "audit-data-exposure")
                result = self.script(package, "scan_repository_data_exposure.py", target,
                                     "--root", str(target), "--scope", "path", "--path", "diagnostic sample.txt")
                self.assertEqual(result.returncode, 0, "Installed scanner failed; child output suppressed")
                payload = json.loads(result.stdout)
                self.assertTrue(any(item["category"] == "email-address" for item in payload["candidates"]))
                self.assertTrue(canary not in result.stdout + result.stderr, "Scanner leaked synthetic private evidence")

    def test_missing_and_repository_only_references_fail_independent_copy(self):
        package = self.root / "synthetic skill"
        package.mkdir()
        (self.root / "outside.md").write_text("Repository-only reference", encoding="utf-8")
        for link in ("missing.md", "../outside.md"):
            with self.subTest(link=link):
                (package / "SKILL.md").write_text(f"[required reference]({link})\n", encoding="utf-8")
                with self.assertRaises(offline.ContentValidationError):
                    validate_resources(package)

    def test_unsafe_and_overlapping_copy_destinations_are_rejected(self):
        source = self.root / "source"
        source.mkdir()
        (source / "SKILL.md").write_text("Fixture", encoding="utf-8")
        occupied = self.root / "occupied"
        occupied.mkdir()
        (occupied / "user.txt").write_text("Keep", encoding="utf-8")
        for target in (source, source / "child", self.root, occupied, self.root / ".." / "escape"):
            with self.subTest(case=target.name):
                with self.assertRaises(state.StateError):
                    state.copy_tree(source, target)
        self.assertEqual((occupied / "user.txt").read_text(encoding="utf-8"), "Keep")

    def test_linked_package_is_not_followed_when_supported(self):
        package = self.root / "linked skill"
        package.mkdir()
        outside = self.root / "outside.md"
        outside.write_text("Keep", encoding="utf-8")
        try:
            (package / "SKILL.md").symlink_to(outside)
        except OSError:
            self.skipTest("Host does not permit creating this symlink")
        with self.assertRaises(state.StateError):
            validate_resources(package)

    def test_cleanup_requires_ownership_and_reports_failure(self):
        bundle = self.root / "owned bundle"
        bundle.mkdir()
        token = secrets.token_hex(16)
        marker = {"schemaVersion": 1, "token": token, "root": str(bundle), "source": str(ROOT)}
        (bundle / state.OWNER_MARKER).write_text(json.dumps(marker), encoding="utf-8")
        with self.assertRaises(state.StateError):
            state.cleanup_owned(bundle, "incorrect", ROOT)
        with mock.patch.object(state.shutil, "rmtree", side_effect=PermissionError):
            with self.assertRaises(state.StateError) as caught:
                state.cleanup_owned(bundle, token, ROOT)
        self.assertEqual(caught.exception.code, "cleanup-failed")
        self.assertTrue(bundle.is_dir())
        state.cleanup_owned(bundle, token, ROOT)
        self.assertFalse(bundle.exists())

    @unittest.skipUnless(os.name == "nt", "Windows junction control")
    def test_directory_junction_is_rejected_without_following_it(self):
        import _winapi

        package = self.root / "junction skill"
        package.mkdir()
        outside = self.root / "outside resources"
        outside.mkdir()
        (outside / "keep.md").write_text("Unrelated resource", encoding="utf-8")
        junction = package / "references"
        _winapi.CreateJunction(str(outside), str(junction))
        try:
            with self.assertRaises(state.StateError):
                validate_resources(package)
            self.assertEqual((outside / "keep.md").read_text(encoding="utf-8"), "Unrelated resource")
        finally:
            # Remove this exact owned junction, never its target tree.
            os.rmdir(junction)

    def test_offline_launch_canary_blocks_models_installers_and_services(self):
        for args in (["codex", "exec", "canary"], ["npm", "install"], ["node", "server.js"],
                     ["npx", "skills", "add", "canary"], [sys.executable, "-c", "raise SystemExit"]):
            with self.subTest(program=Path(args[0]).name):
                with self.assertRaisesRegex(AssertionError, "launch blocked"):
                    subprocess.Popen(args)


if __name__ == "__main__":
    unittest.main()
