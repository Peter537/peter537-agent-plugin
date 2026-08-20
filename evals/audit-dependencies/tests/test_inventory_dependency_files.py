from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = (
    REPOSITORY_ROOT
    / "skills"
    / "audit-dependencies"
    / "scripts"
    / "inventory_dependency_files.py"
)


def load_inventory_module():
    specification = importlib.util.spec_from_file_location(
        "audit_dependencies_inventory", SCRIPT_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("Cannot load dependency inventory module.")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


inventory_module = load_inventory_module()


def isolated_git_environment() -> dict[str, str]:
    environment = {
        name: value for name, value in os.environ.items() if not name.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_AUTHOR_EMAIL": "fixture@localhost",
            "GIT_AUTHOR_NAME": "Dependency Inventory Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@localhost",
            "GIT_COMMITTER_NAME": "Dependency Inventory Fixture",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def run_git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgSign=false",
            "-c",
            f"core.hooksPath={os.devnull}",
            "-c",
            "core.autocrlf=false",
            *arguments,
        ],
        cwd=repository,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=isolated_git_environment(),
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout


def initialize_repository(repository: Path) -> None:
    repository.mkdir(parents=True, exist_ok=True)
    run_git(repository, "init", "--quiet", "--initial-branch=main", "--template=")
    (repository / "README.md").write_text("Fixture\n", encoding="utf-8")
    run_git(repository, "add", "--all")
    run_git(repository, "commit", "--quiet", "-m", "Base fixture")


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


class InventoryDependencyFilesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(
            prefix="audit-dependencies-test-"
        )
        self.root = Path(self.temporary_directory.name) / "private-workspace-canary"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, relative_path: str, contents: str = "") -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        return path

    def run_main(self, *arguments: str) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            return_code = inventory_module.main(arguments)
        return return_code, stdout.getvalue(), stderr.getvalue()

    def test_json_output_is_versioned_redacted_and_root_relative(self) -> None:
        self.write("package.json", '{"name":"fixture","dependencies":{}}')

        return_code, stdout, stderr = self.run_main(str(self.root), "--format", "json")

        self.assertEqual(0, return_code, stderr)
        payload = json.loads(stdout)
        self.assertEqual(1, payload["schemaVersion"])
        self.assertEqual(".", payload["root"])
        self.assertIsInstance(payload["gaps"], list)
        self.assertIsInstance(payload["exclusions"], list)
        self.assertNotIn(str(self.root), stdout)

    def test_text_output_does_not_disclose_absolute_root(self) -> None:
        self.write("requirements.txt", "example-package==1.0.0\n")

        return_code, stdout, stderr = self.run_main(str(self.root), "--format", "text")

        self.assertEqual(0, return_code, stderr)
        self.assertIn("Root: .", stdout)
        self.assertNotIn(str(self.root), stdout)

    def test_monorepo_packages_and_vscode_extensions_are_discovered(self) -> None:
        self.write("packages/client/package.json", '{"name":"client"}')
        self.write(".vscode/extensions.json", '{"recommendations":["vendor.tool"]}')
        self.write("node_modules/ignored/package.json", '{"name":"ignored"}')

        payload = inventory_module.inventory(self.root)
        paths = {item["path"] for item in payload["items"]}

        self.assertIn("packages/client/package.json", paths)
        self.assertIn(".vscode/extensions.json", paths)
        self.assertNotIn("node_modules/ignored/package.json", paths)
        self.assertTrue(
            any(
                exclusion["path"] == "node_modules"
                and exclusion["category"] == "generated-or-cache-name-policy"
                for exclusion in payload["exclusions"]
            )
        )

    def test_ambiguous_source_shaped_exclusions_are_explicit_and_relative(self) -> None:
        self.write("bin/service/package.json", '{"name":"source-service"}')
        self.write("env/tool/pyproject.toml", "[project]\nname='source-tool'\n")
        self.write("build/client/Cargo.toml", "[package]\nname='source-client'\n")
        self.write("node_modules/cache/package.json", '{"name":"cache"}')

        payload = inventory_module.inventory(self.root)

        paths = {item["path"] for item in payload["items"]}
        self.assertFalse(
            {
                "bin/service/package.json",
                "env/tool/pyproject.toml",
                "build/client/Cargo.toml",
                "node_modules/cache/package.json",
            }
            & paths
        )
        exclusions = {record["path"]: record for record in payload["exclusions"]}
        self.assertEqual(
            {"bin", "build", "env", "node_modules"},
            {path for path in exclusions if path in {"bin", "build", "env", "node_modules"}},
        )
        self.assertTrue(
            all(
                record["category"] == "generated-or-cache-name-policy"
                and "confirm" in record["reason"].lower()
                for record in exclusions.values()
            )
        )
        serialized = json.dumps(payload, sort_keys=True)
        self.assertNotIn(str(self.root), serialized)
        self.assertEqual(4, payload["summary"]["exclusion_count"])

    def test_malformed_package_manifest_is_reported_as_a_gap(self) -> None:
        self.write("package.json", "{not-json")

        payload = inventory_module.inventory(self.root)

        self.assertTrue(
            any(
                gap["path"] == "package.json"
                and gap["category"] == "malformed-input"
                for gap in payload["gaps"]
            )
        )

    def test_private_and_credential_bearing_locators_are_redacted(self) -> None:
        secret = f"PRIVATE-LOCATOR-CANARY-{secrets.token_hex(18)}"
        self.write(
            ".gitmodules",
            "[submodule \"private\"]\n"
            "\tpath = vendor/private\n"
            f"\turl = https://user:{secret}@git.example.invalid/team/private.git\n",
        )
        self.write(
            ".github/workflows/build.yml",
            "jobs:\n  build:\n    steps:\n"
            f"      - uses: private-org/{secret}@v1\n",
        )
        self.write(
            "compose.yml",
            f"services:\n  app:\n    image: registry.example.invalid/{secret}:1\n",
        )

        return_code, stdout, stderr = self.run_main(str(self.root), "--format", "json")

        self.assertEqual(0, return_code, stderr)
        self.assertNotIn(secret, stdout)
        payload = json.loads(stdout)
        redacted = [
            item
            for item in payload["items"]
            if item.get("locator_status") == "present-redacted"
        ]
        self.assertGreaterEqual(len(redacted), 3)
        self.assertTrue(all("locator" not in item for item in redacted))

    def test_symlinked_file_outside_root_is_not_read(self) -> None:
        outside = Path(self.temporary_directory.name) / "outside-package.json"
        secret = f"OUTSIDE-FILE-CANARY-{secrets.token_hex(18)}"
        outside.write_text(f'{{"name":"{secret}"}}', encoding="utf-8")
        link = self.root / "package.json"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"File symlinks are unavailable: {exc}")

        return_code, stdout, stderr = self.run_main(str(self.root), "--format", "json")

        self.assertEqual(0, return_code, stderr)
        self.assertNotIn(secret, stdout)
        payload = json.loads(stdout)
        self.assertNotIn("package.json", {item["path"] for item in payload["items"]})
        self.assertTrue(
            any(
                gap["path"] == "package.json"
                and gap["category"] == "link-or-reparse-not-followed"
                for gap in payload["gaps"]
            )
        )

    def test_symlinked_directory_outside_root_is_not_traversed(self) -> None:
        outside = Path(self.temporary_directory.name) / "outside-tree"
        outside.mkdir()
        secret = f"OUTSIDE-DIRECTORY-CANARY-{secrets.token_hex(18)}"
        (outside / "package.json").write_text(
            f'{{"name":"{secret}"}}', encoding="utf-8"
        )
        link = self.root / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Directory symlinks are unavailable: {exc}")

        return_code, stdout, stderr = self.run_main(str(self.root), "--format", "json")

        self.assertEqual(0, return_code, stderr)
        self.assertNotIn(secret, stdout)
        payload = json.loads(stdout)
        self.assertTrue(
            any(
                gap["path"] == "linked"
                and gap["category"] == "link-or-reparse-not-followed"
                for gap in payload["gaps"]
            )
        )

    def test_symlinked_root_is_rejected_without_disclosing_host_path(self) -> None:
        self.write("package.json", '{"name":"fixture"}')
        link = Path(self.temporary_directory.name) / "linked-root-canary"
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"Directory symlinks are unavailable: {exc}")

        return_code, stdout, stderr = self.run_main(str(link), "--format", "json")

        self.assertEqual(2, return_code)
        self.assertEqual("", stdout)
        self.assertNotIn(str(link), stderr)
        self.assertNotIn(str(self.root), stderr)

    def test_supported_discovery_families_and_deterministic_sorting(self) -> None:
        expected = {
            "package-lock.json": "javascript",
            "pyproject.toml": "python",
            "Directory.Packages.props": "dotnet",
            "go.sum": "go",
            "Cargo.lock": "rust",
            "pom.xml": "jvm",
            "composer.lock": "php",
            "Gemfile.lock": "ruby",
            "pubspec.lock": "dart",
            "mix.lock": "elixir",
            "cabal.project.freeze": "haskell",
            "renv.lock": "r",
            "vcpkg.json": "cpp",
            "Package.resolved": "swift",
            ".terraform.lock.hcl": "terraform",
            "flake.lock": "nix",
            "Chart.lock": "helm",
            ".pre-commit-config.yaml": "pre-commit",
            "mcp.json": "mcp",
        }
        for path in reversed(list(expected)):
            self.write(path, "{}\n")

        first = inventory_module.inventory(self.root)
        second = inventory_module.inventory(self.root)
        discovered = {item["path"]: item["ecosystem"] for item in first["items"]}

        for path, ecosystem in expected.items():
            self.assertEqual(ecosystem, discovered.get(path), path)
        self.assertEqual(first, second)
        paths = [item["path"] for item in first["items"]]
        self.assertEqual(paths, sorted(paths, key=str.casefold))

    def test_git_is_the_only_subprocess_family_and_failure_becomes_a_gap(self) -> None:
        self.write("package.json", '{"name":"fixture"}')

        calls: list[list[str]] = []

        def fake_run(command, **kwargs):
            calls.append(list(command))
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="not a repository")

        with mock.patch.object(inventory_module.subprocess, "run", side_effect=fake_run):
            payload = inventory_module.inventory(self.root)

        self.assertTrue(calls)
        self.assertTrue(all(command[0] == "git" for command in calls))
        self.assertTrue(
            any(gap["category"] == "git-metadata-unavailable" for gap in payload["gaps"])
        )

    def test_git_environment_cannot_redirect_scope_or_execute_fsmonitor(self) -> None:
        initialize_repository(self.root)
        hostile = Path(self.temporary_directory.name) / "hostile"
        initialize_repository(hostile)
        hostile_head = run_git(hostile, "rev-parse", "HEAD").strip()
        run_git(
            hostile,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{hostile_head},private-hostile-module",
        )
        hook, marker = create_fsmonitor_hook(Path(self.temporary_directory.name))
        run_git(self.root, "config", "core.fsmonitor", hook.as_posix())
        token = f"HOSTILE-{secrets.token_hex(16)}"

        inherited = {
            "GIT_DIR": str(hostile / ".git"),
            "GIT_WORK_TREE": str(hostile),
            "GIT_INDEX_FILE": str(hostile / ".git" / "index"),
            "GIT_CONFIG_PARAMETERS": f"'core.fsmonitor={hook.as_posix()}'",
            "HOSTILE_INVENTORY_CANARY": token,
        }
        probe_environment = isolated_git_environment()
        probe_environment.update(inherited)
        probe = subprocess.run(
            ["git", "-C", str(self.root), "status", "--short"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            env=probe_environment,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr)
        self.assertTrue(marker.exists(), "The hostile fsmonitor setup was not exercised.")
        marker.unlink()

        with mock.patch.dict(os.environ, inherited, clear=False):
            return_code, stdout, stderr = self.run_main(str(self.root), "--format", "json")

        self.assertEqual(return_code, 0, stderr)
        self.assertFalse(marker.exists())
        self.assertNotIn("private-hostile-module", stdout)
        self.assertNotIn(token, stdout)
        self.assertNotIn(str(hostile), stdout)

    def test_invalid_root_error_is_redacted(self) -> None:
        missing = self.root / "private-missing-canary"

        return_code, stdout, stderr = self.run_main(str(missing), "--format", "json")

        self.assertEqual(2, return_code)
        self.assertEqual("", stdout)
        self.assertNotIn(str(missing), stderr)
        self.assertIn("root", stderr.lower())


if __name__ == "__main__":
    unittest.main()
