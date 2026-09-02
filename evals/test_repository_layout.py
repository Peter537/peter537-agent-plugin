"""Tests for the repository layout validator.

The fixtures are deliberately small and are created only under the operating
system's temporary directory. They model the structural contract rather than
copying the real repository.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


VALIDATOR = Path(__file__).with_name("validate_repository_layout.py")


class RepositoryLayoutValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="p537-layout-eval-"
        )
        self.root = Path(self._temporary_directory.name) / "fixture"
        self._create_valid_repository(self.root)

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def run_validator(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(VALIDATOR),
                "--root",
                str(self.root),
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def assert_failed_with(self, result: subprocess.CompletedProcess[str], term: str) -> None:
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(term.casefold(), (result.stdout + result.stderr).casefold())

    def test_valid_repository_passes_in_strict_mode(self) -> None:
        result = self.run_validator("--strict-groups")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS:", result.stdout)

    def test_nested_skill_package_is_rejected(self) -> None:
        self._write_skill(self.root / "skills" / "category" / "nested", "nested")

        result = self.run_validator()

        self.assert_failed_with(result, "nested")

    def test_nested_linked_skill_package_is_rejected_when_links_are_supported(self) -> None:
        target = self.root / "linked-package-source"
        self._write_skill(target, "linked-package")
        linked_package = self.root / "skills" / "alpha" / "linked-package"
        try:
            linked_package.symlink_to(target, target_is_directory=True)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"directory links are unavailable: {error.__class__.__name__}")

        result = self.run_validator()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        diagnostics = (result.stdout + result.stderr).casefold()
        self.assertTrue(
            "link" in diagnostics or "reparse" in diagnostics,
            result.stdout + result.stderr,
        )

    def test_hidden_skill_package_is_rejected(self) -> None:
        self._write_skill(self.root / "skills" / ".hidden", ".hidden")

        result = self.run_validator()

        self.assert_failed_with(result, "hidden")

    def test_missing_eval_suite_is_rejected(self) -> None:
        (self.root / "evals" / "bravo" / "cases.json").unlink()
        (self.root / "evals" / "bravo").rmdir()

        result = self.run_validator()

        self.assert_failed_with(result, "eval")

    def test_duplicate_group_assignment_is_rejected(self) -> None:
        configuration = self._read_group_configuration()
        configuration["groupings"].append(
            {
                "title": "Second group",
                "description": "A duplicate assignment.",
                "skills": ["alpha"],
            }
        )
        self._write_json(self.root / "skills.sh.json", configuration)

        result = self.run_validator()

        self.assert_failed_with(result, "duplicate")

    def test_unknown_group_assignment_is_rejected(self) -> None:
        configuration = self._read_group_configuration()
        configuration["groupings"][0]["skills"].append("not-a-skill")
        self._write_json(self.root / "skills.sh.json", configuration)

        result = self.run_validator()

        self.assert_failed_with(result, "unknown")

    def test_frontmatter_name_mismatch_is_rejected(self) -> None:
        self._write_skill(self.root / "skills" / "alpha", "different-name")

        result = self.run_validator()

        self.assert_failed_with(result, "name")

    def test_ungrouped_skill_warns_by_default_and_fails_in_strict_mode(self) -> None:
        configuration = self._read_group_configuration()
        configuration["groupings"][1]["skills"].remove("bravo")
        self._write_json(self.root / "skills.sh.json", configuration)

        development_result = self.run_validator()
        release_result = self.run_validator("--strict-groups")

        self.assertEqual(
            development_result.returncode,
            0,
            development_result.stdout + development_result.stderr,
        )
        self.assertIn("WARNING:", development_result.stdout)
        self.assertIn("ungrouped", development_result.stdout.casefold())
        self.assert_failed_with(release_result, "ungrouped")

    def test_missing_catalog_link_is_rejected(self) -> None:
        catalog = self.root / "docs" / "skills" / "README.md"
        catalog.write_text(
            catalog.read_text(encoding="utf-8").replace(
                "[Bravo evaluation](../../evals/bravo/cases.json)\n", ""
            ),
            encoding="utf-8",
        )

        result = self.run_validator()

        self.assert_failed_with(result, "catalog")

    def test_catalog_pairs_must_remain_under_their_configured_groups(self) -> None:
        catalog = self.root / "docs" / "skills" / "README.md"
        catalog.write_text(
            """# Skill Catalog

## Example group

[Bravo](../../skills/bravo/SKILL.md)
[Bravo evaluation](../../evals/bravo/cases.json)

## Second group

[Alpha](../../skills/alpha/SKILL.md)
[Alpha evaluation](../../evals/alpha/cases.json)
""",
            encoding="utf-8",
        )

        result = self.run_validator()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        diagnostics = (result.stdout + result.stderr).casefold()
        self.assertIn("catalog", diagnostics)
        self.assertIn("group", diagnostics)

    def test_manifest_skill_path_must_remain_canonical(self) -> None:
        self._write_json(
            self.root / ".codex-plugin" / "plugin.json",
            {"skills": "./skills/grouped/"},
        )

        result = self.run_validator()

        self.assert_failed_with(result, "./skills/")

    def _read_group_configuration(self) -> dict[str, object]:
        return json.loads((self.root / "skills.sh.json").read_text(encoding="utf-8"))

    @classmethod
    def _create_valid_repository(cls, root: Path) -> None:
        cls._write_skill(root / "skills" / "alpha", "alpha")
        cls._write_skill(root / "skills" / "bravo", "bravo")

        for slug in ("alpha", "bravo"):
            cls._write_json(
                root / "evals" / slug / "cases.json",
                {"schemaVersion": 1, "skill": slug},
            )

        cls._write_json(
            root / "skills.sh.json",
            {
                "notGrouped": "bottom",
                "groupings": [
                    {
                        "title": "Example group",
                        "description": "A compact synthetic group.",
                        "skills": ["alpha"],
                    },
                    {
                        "title": "Second group",
                        "description": "A second compact synthetic group.",
                        "skills": ["bravo"],
                    },
                ],
            },
        )
        cls._write_json(
            root / ".codex-plugin" / "plugin.json",
            {"skills": "./skills/"},
        )

        catalog = """# Skill Catalog

## Example group

[Alpha](../../skills/alpha/SKILL.md)
[Alpha evaluation](../../evals/alpha/cases.json)

## Second group

[Bravo](../../skills/bravo/SKILL.md)
[Bravo evaluation](../../evals/bravo/cases.json)
"""
        catalog_path = root / "docs" / "skills" / "README.md"
        catalog_path.parent.mkdir(parents=True, exist_ok=True)
        catalog_path.write_text(catalog, encoding="utf-8")

    @staticmethod
    def _write_skill(directory: Path, name: str) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "SKILL.md").write_text(
            "\n".join(
                (
                    "---",
                    f"name: {name}",
                    "description: Synthetic layout fixture.",
                    "license: MIT",
                    "---",
                    "",
                    f"# {name}",
                    "",
                )
            ),
            encoding="utf-8",
        )

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
