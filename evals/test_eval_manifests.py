"""Tests for the common evaluation-manifest validator.

The fixtures are deliberately synthetic and live only beneath the operating
system's temporary directory. They exercise the shared manifest contract
without copying a distributed skill or executing any declared command.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


VALIDATOR = Path(__file__).with_name("validate_eval_manifests.py")


def _load_validator_module() -> object:
    spec = importlib.util.spec_from_file_location(
        "p537_validate_eval_manifests", VALIDATOR
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the eval-manifest validator module.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR_MODULE = _load_validator_module()


class EvalManifestValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="p537-eval-manifest-"
        )
        self.temporary_root = Path(self._temporary_directory.name)
        self.root = self._new_repository("fixture", ("alpha",))

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def run_validator(
        self, root: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(VALIDATOR),
                "--root",
                str(root or self.root),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def assert_contract_error(
        self,
        result: subprocess.CompletedProcess[str],
        *terms: str,
    ) -> None:
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        diagnostics = (result.stdout + result.stderr).casefold()
        self.assertIn("error", diagnostics, result.stdout + result.stderr)
        for term in terms:
            self.assertIn(term.casefold(), diagnostics, result.stdout + result.stderr)

    def test_valid_heterogeneous_manifests_pass(self) -> None:
        root = self._new_repository(
            "heterogeneous", ("alpha", "bravo", "charlie", "delta")
        )

        alpha = self._read_manifest(root, "alpha")
        alpha["cases"][0]["git"] = {
            "mode": "dirty",
            "expectedStatus": [" M src/example.py"],
            "canaryPath": "ignored-data/synthetic.json",
            "suiteSpecificPolicy": {"preserveBranches": True},
        }
        self._write_manifest(root, "alpha", alpha)

        bravo = self._read_manifest(root, "bravo")
        bravo["suite"] = "bravo"
        bravo["cases"][0]["expected"]["outcome"] = "reviewed"
        bravo["cases"][0]["runtimeCanary"] = {
            "path": "packet.json",
            "placeholder": "[SYNTHETIC_RUNTIME_CANARY]",
            "packetPolicy": {"offline": True, "maximumSources": 2},
        }
        self._write_manifest(root, "bravo", bravo)

        charlie = self._read_manifest(root, "charlie")
        charlie["cases"][0]["verificationCommands"] = self._safe_commands()
        charlie["cases"][0]["authorizedPaths"] = [
            "src/generated/output.py",
            "tests/test_output.py",
        ]
        self._write_manifest(root, "charlie", charlie)

        delta = self._read_manifest(root, "delta")
        delta["liveCases"] = [
            {
                "id": "live-public-smoke",
                "authorizationRequired": True,
                "enabledByDefault": False,
                "requiredSignals": ["public input", "no tracked output"],
            }
        ]
        self._write_manifest(root, "delta", delta)

        result = self.run_validator(root)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS:", result.stdout)
        self.assertIn("4 suites", result.stdout)
        self.assertIn("4 cases", result.stdout)
        self.assertIn("8 triggers", result.stdout)
        self.assertIn("1 live", result.stdout)

    def test_suite_and_expected_outcome_are_optional(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        self.assertNotIn("suite", manifest)
        self.assertNotIn("outcome", manifest["cases"][0]["expected"])

        result = self.run_validator()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_matching_optional_suite_and_outcome_pass(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["suite"] = "alpha"
        manifest["cases"][0]["expected"]["outcome"] = "verified"
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unknown_top_level_section_is_rejected(self) -> None:
        canary = "TOP_" + secrets.token_hex(12)
        manifest = self._read_manifest(self.root, "alpha")
        manifest[canary] = []
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "unsupported top-level")
        self.assertNotIn(canary, result.stdout + result.stderr)

    def test_arbitrary_manifest_keys_are_redacted_from_diagnostics(self) -> None:
        canary = "KEY_" + secrets.token_hex(12)
        manifest = self._read_manifest(self.root, "alpha")
        manifest["cases"][0][canary] = {"path": "../outside"}
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "path metadata")
        self.assertNotIn(canary, result.stdout + result.stderr)

    def test_suite_name_must_match_directory(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["suite"] = "bravo"
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "suite")

    def test_schema_version_must_be_one(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["schemaVersion"] = 2
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "schemaVersion")

    def test_required_top_level_fields_are_enforced(self) -> None:
        for field in ("schemaVersion", "suiteExpectations", "cases", "triggerCases"):
            with self.subTest(field=field):
                root = self._new_repository(f"missing-top-{field}", ("alpha",))
                manifest = self._read_manifest(root, "alpha")
                del manifest[field]
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, field)

    def test_suite_expectation_fields_must_be_nonempty_and_well_typed(self) -> None:
        invalid_values: tuple[tuple[str, object], ...] = (
            ("requiredSignals", []),
            ("prohibitedSignals", "not-an-array"),
            ("repositoryState", ""),
        )
        for field, value in invalid_values:
            with self.subTest(field=field):
                root = self._new_repository(
                    f"invalid-suite-expectations-{field}", ("alpha",)
                )
                manifest = self._read_manifest(root, "alpha")
                manifest["suiteExpectations"][field] = value
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "suiteExpectations", field)

        for field in ("requiredSignals", "prohibitedSignals", "repositoryState"):
            with self.subTest(missing=field):
                root = self._new_repository(
                    f"missing-suite-expectations-{field}", ("alpha",)
                )
                manifest = self._read_manifest(root, "alpha")
                del manifest["suiteExpectations"][field]
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "suiteExpectations", field)

    def test_behavioral_case_fields_are_required(self) -> None:
        for field in ("id", "description", "prompt", "fixture", "expected"):
            with self.subTest(field=field):
                root = self._new_repository(f"missing-case-{field}", ("alpha",))
                manifest = self._read_manifest(root, "alpha")
                del manifest["cases"][0][field]
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "cases", field)

    def test_expected_fields_must_be_nonempty_and_well_typed(self) -> None:
        invalid_values: tuple[tuple[str, object], ...] = (
            ("requiredSignals", []),
            ("prohibitedSignals", "not-an-array"),
            ("repositoryState", ""),
        )
        for field, value in invalid_values:
            with self.subTest(field=field):
                root = self._new_repository(f"invalid-expected-{field}", ("alpha",))
                manifest = self._read_manifest(root, "alpha")
                manifest["cases"][0]["expected"][field] = value
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "expected", field)

    def test_trigger_fields_are_required_and_boolean_is_strict(self) -> None:
        for field in ("id", "prompt", "expectActivation"):
            with self.subTest(field=field):
                root = self._new_repository(f"missing-trigger-{field}", ("alpha",))
                manifest = self._read_manifest(root, "alpha")
                del manifest["triggerCases"][0][field]
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "triggerCases", field)

        manifest = self._read_manifest(self.root, "alpha")
        manifest["triggerCases"][0]["expectActivation"] = 1
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "expectActivation")

    def test_positive_and_negative_trigger_are_both_required(self) -> None:
        for activation in (True, False):
            with self.subTest(activation=activation):
                root = self._new_repository(
                    f"single-trigger-kind-{activation}", ("alpha",)
                )
                manifest = self._read_manifest(root, "alpha")
                for trigger in manifest["triggerCases"]:
                    trigger["expectActivation"] = activation
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "trigger")

    def test_ids_must_be_lowercase_slugs(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["cases"][0]["id"] = "Not A Slug"
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "id")

    def test_ids_must_be_unique_across_sections_within_suite(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["triggerCases"][0]["id"] = manifest["cases"][0]["id"]
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "duplicate", "id")

    def test_same_id_in_different_suites_is_allowed(self) -> None:
        root = self._new_repository("cross-suite-ids", ("alpha", "bravo"))

        result = self.run_validator(root)

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_and_unsafe_fixture_references_are_rejected(self) -> None:
        invalid_fixtures = {
            "missing": "not-present",
            "traversal": "../outside",
            "git": ".git/private",
        }
        for label, fixture in invalid_fixtures.items():
            with self.subTest(label=label):
                root = self._new_repository(f"fixture-{label}", ("alpha",))
                manifest = self._read_manifest(root, "alpha")
                manifest["cases"][0]["fixture"] = fixture
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "fixture")

    def test_linked_fixture_is_rejected_when_links_are_supported(self) -> None:
        fixture_root = self.root / "evals" / "alpha" / "fixtures"
        outside = self.temporary_root / "outside-fixture"
        outside.mkdir()
        (outside / "input.txt").write_text("outside\n", encoding="utf-8")
        linked = fixture_root / "linked"
        try:
            linked.symlink_to(outside, target_is_directory=True)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"directory links are unavailable: {error.__class__.__name__}")

        manifest = self._read_manifest(self.root, "alpha")
        manifest["cases"][0]["fixture"] = "linked"
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        diagnostics = (result.stdout + result.stderr).casefold()
        self.assertIn("fixture", diagnostics)
        self.assertTrue(
            "link" in diagnostics or "reparse" in diagnostics,
            result.stdout + result.stderr,
        )

    def test_nested_linked_fixture_entry_is_rejected_when_supported(self) -> None:
        outside = self.temporary_root / "outside-nested-fixture"
        outside.mkdir()
        (outside / "input.txt").write_text("outside\n", encoding="utf-8")
        linked = self.root / "evals" / "alpha" / "fixtures" / "basic" / "linked"
        try:
            linked.symlink_to(outside, target_is_directory=True)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"directory links are unavailable: {error.__class__.__name__}")

        result = self.run_validator()

        self.assert_contract_error(result, "fixture", "link")

    def test_windows_reparse_attribute_is_detected_when_available(self) -> None:
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        if not reparse_flag:
            self.skipTest("Windows reparse attributes are unavailable")
        metadata = SimpleNamespace(
            st_mode=stat.S_IFDIR,
            st_file_attributes=reparse_flag,
        )
        check = getattr(VALIDATOR_MODULE, "_is_link_or_reparse")

        with mock.patch.object(Path, "lstat", return_value=metadata):
            self.assertTrue(check(Path("synthetic-reparse")))

    def test_link_inspection_errors_fail_closed_without_value_disclosure(self) -> None:
        canary = "LINK_" + secrets.token_hex(12)
        check = getattr(VALIDATOR_MODULE, "_is_link_or_reparse")
        error_type = getattr(VALIDATOR_MODULE, "PathInspectionError")

        with mock.patch.object(
            Path,
            "lstat",
            side_effect=PermissionError(canary),
        ):
            with self.assertRaises(error_type) as raised:
                check(Path("synthetic-uninspectable"))

        self.assertNotIn(canary, str(raised.exception))

    def test_relative_metadata_paths_need_not_exist(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["cases"][0]["authorizedPaths"] = [
            "src/not-materialized/generated.py",
            "tests/not-materialized/test_generated.py",
        ]
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unsafe_known_metadata_paths_are_rejected_and_redacted(self) -> None:
        canary = "METADATA_" + secrets.token_hex(12)
        invalid_paths = {
            "traversal": "../outside.py",
            "absolute": f"C:\\Users\\{canary}\\source.py",
            "alternate-data-stream": "src/data.txt:private",
            "reserved-device": "src/NUL.txt",
        }
        for label, path in invalid_paths.items():
            with self.subTest(label=label):
                root = self._new_repository(f"metadata-path-{label}", ("alpha",))
                manifest = self._read_manifest(root, "alpha")
                manifest["cases"][0]["authorizedPaths"] = [path]
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "authorizedPaths")
                self.assertNotIn(canary, result.stdout + result.stderr)

    def test_private_paths_are_rejected_without_value_disclosure(self) -> None:
        canary = "PRIVATE_" + secrets.token_hex(12)
        manifest = self._read_manifest(self.root, "alpha")
        manifest["cases"][0]["prompt"] = (
            f"Inspect C:\\Users\\{canary}\\repo, file:///home/{canary}/repo, "
            f"[/Users/{canary}/repo], and /root/{canary}."
        )
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        combined = result.stdout + result.stderr
        self.assertNotIn(canary, combined)
        self.assertIn("prompt", combined.casefold())

    def test_private_paths_in_nested_keys_are_rejected_and_redacted(self) -> None:
        canary = "KEY_PATH_" + secrets.token_hex(12)
        manifest = self._read_manifest(self.root, "alpha")
        manifest["cases"][0]["suiteSpecificMetadata"] = {
            f"C:\\Users\\{canary}\\repo": "benign value"
        }
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "personal-home", "<field>")
        self.assertNotIn(canary, result.stdout + result.stderr)

    def test_known_skill_owners_and_provisional_owners_are_accepted(self) -> None:
        self._write_skill(self.root, "bravo")
        manifest = self._read_manifest(self.root, "alpha")
        manifest["triggerCases"][0]["expectedOwner"] = "alpha"
        provisional = (
            "implementation-workflow",
            "legal-guidance",
            "ordinary-implementation",
            "ordinary implementation",
            "release-workflow",
            "repository-analysis",
        )
        for index, owner in enumerate(provisional):
            manifest["triggerCases"].append(
                {
                    "id": f"near-miss-provisional-{index}",
                    "prompt": "A synthetic near miss.",
                    "expectActivation": False,
                    "expectedOwner": owner,
                }
            )
        manifest["triggerCases"][1]["expectedOwner"] = "$bravo"
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unknown_owner_is_rejected(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["triggerCases"][1]["expectedOwner"] = "$unknown-skill"
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "expectedOwner")

    def test_positive_owner_must_match_suite(self) -> None:
        self._write_skill(self.root, "bravo")
        manifest = self._read_manifest(self.root, "alpha")
        manifest["triggerCases"][0]["expectedOwner"] = "$bravo"
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "expectedOwner")

    def test_negative_owner_must_not_name_suite(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["triggerCases"][1]["expectedOwner"] = "$alpha"
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "expectedOwner")

    def test_both_live_authorization_shapes_pass(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["liveCases"] = [
            {
                "id": "live-authorized-boolean",
                "authorizationRequired": True,
                "enabledByDefault": False,
                "requiredSignals": ["explicit approval"],
            },
            {
                "id": "live-authorized-string",
                "authorization": "separate-explicit-approval-required",
                "trackOutput": False,
                "expectedSignals": ["temporary output only"],
            },
        ]
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_conflicting_live_authorization_is_rejected(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["liveCases"] = [
            {
                "id": "live-conflicting-authorization",
                "authorizationRequired": True,
                "authorization": "implicit",
                "requiredSignals": ["signal"],
            }
        ]
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "authorization")

    def test_live_cases_require_authorization_and_signals(self) -> None:
        invalid_live_cases = {
            "missing-authorization": {
                "id": "live-invalid",
                "requiredSignals": ["signal"],
            },
            "false-authorization": {
                "id": "live-invalid",
                "authorizationRequired": False,
                "requiredSignals": ["signal"],
            },
            "missing-signals": {
                "id": "live-invalid",
                "authorizationRequired": True,
            },
            "bad-authorization-string": {
                "id": "live-invalid",
                "authorization": "implicit",
                "requiredSignals": ["signal"],
            },
        }
        for label, live_case in invalid_live_cases.items():
            with self.subTest(label=label):
                root = self._new_repository(f"live-{label}", ("alpha",))
                manifest = self._read_manifest(root, "alpha")
                manifest["liveCases"] = [live_case]
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "liveCases")

    def test_live_cases_cannot_be_enabled_or_tracked_by_default(self) -> None:
        for field in ("enabledByDefault", "trackOutput"):
            with self.subTest(field=field):
                root = self._new_repository(f"live-unsafe-{field}", ("alpha",))
                manifest = self._read_manifest(root, "alpha")
                manifest["liveCases"] = [
                    {
                        "id": "live-invalid",
                        "authorizationRequired": True,
                        "requiredSignals": ["signal"],
                        field: True,
                    }
                ]
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, field)

    def test_live_fixture_is_validated_when_present(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["liveCases"] = [
            {
                "id": "live-missing-fixture",
                "authorizationRequired": True,
                "requiredSignals": ["signal"],
                "fixture": "missing",
            }
        ]
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assert_contract_error(result, "fixture")

    def test_safe_verification_commands_pass(self) -> None:
        manifest = self._read_manifest(self.root, "alpha")
        manifest["cases"][0]["verificationCommands"] = self._safe_commands()
        self._write_manifest(self.root, "alpha", manifest)

        result = self.run_validator()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_verification_command_shape_is_enforced(self) -> None:
        invalid_shapes: tuple[tuple[str, object], ...] = (
            ("not-object", []),
            ("missing-after", {"before": []}),
            ("not-array", {"before": "python", "after": []}),
            (
                "missing-purpose",
                {"before": [{"argv": ["python", "check.py"]}], "after": []},
            ),
            (
                "argv-not-array",
                {
                    "before": [{"purpose": "check", "argv": "python check.py"}],
                    "after": [],
                },
            ),
            (
                "empty-argv",
                {"before": [{"purpose": "check", "argv": []}], "after": []},
            ),
        )
        for label, commands in invalid_shapes:
            with self.subTest(label=label):
                root = self._new_repository(f"commands-shape-{label}", ("alpha",))
                manifest = self._read_manifest(root, "alpha")
                manifest["cases"][0]["verificationCommands"] = commands
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "verificationCommands")

    def test_unsafe_verification_commands_are_rejected(self) -> None:
        canary = "COMMAND_" + secrets.token_hex(12)
        invalid_argvs = {
            "unknown-family": ["node", "check.js"],
            "shell-launcher": ["powershell", "-Command", "Get-ChildItem"],
            "inline-python": ["python", "-c", "print('unsafe')"],
            "clustered-inline-python": ["python", "-Ic", "print('unsafe')"],
            "stdin-python": ["python", "-"],
            "installer": ["python", "-m", "pip", "install", "package"],
            "installer-module": [
                "python",
                "-m",
                "pip.__main__",
                "install",
                "package",
            ],
            "traversal": ["python", "../outside.py"],
            "attached-traversal": ["python", "check.py", "--output=../outside"],
            "shell-operator": ["python", "check.py", "&&", "other"],
            "absolute": ["python", f"C:\\Users\\{canary}\\check.py"],
            "attached-absolute": [
                "python",
                "check.py",
                f"--output=C:\\Users\\{canary}\\result.json",
            ],
            "colon-attached-absolute": [
                "python",
                "check.py",
                f"--output:C:\\Users\\{canary}\\result.json",
            ],
            "short-attached-traversal": [
                "python",
                "check.py",
                "-o../outside",
            ],
            "response-file-traversal": [
                "dotnet",
                "test",
                "@../outside.rsp",
            ],
            "dotnet-restore-switch": [
                "dotnet",
                "msbuild",
                "Fixture.csproj",
                "-restore",
            ],
        }
        for label, argv in invalid_argvs.items():
            with self.subTest(label=label):
                root = self._new_repository(f"commands-unsafe-{label}", ("alpha",))
                manifest = self._read_manifest(root, "alpha")
                manifest["cases"][0]["verificationCommands"] = {
                    "before": [{"purpose": "unsafe candidate", "argv": argv}],
                    "after": [
                        {
                            "purpose": "safe comparison",
                            "argv": ["python", "check.py"],
                        }
                    ],
                }
                self._write_manifest(root, "alpha", manifest)

                result = self.run_validator(root)

                self.assert_contract_error(result, "verificationCommands")
                self.assertNotIn(canary, result.stdout + result.stderr)

    def test_malformed_json_and_unusable_root_return_two(self) -> None:
        manifest_path = self.root / "evals" / "alpha" / "cases.json"
        manifest_path.write_text("{not-json\n", encoding="utf-8")

        malformed_result = self.run_validator()
        missing_result = self.run_validator(self.temporary_root / "does-not-exist")

        self.assertEqual(
            malformed_result.returncode,
            2,
            malformed_result.stdout + malformed_result.stderr,
        )
        self.assertEqual(
            missing_result.returncode,
            2,
            missing_result.stdout + missing_result.stderr,
        )

    def test_validation_is_read_only(self) -> None:
        before = self._snapshot(self.root)

        result = self.run_validator()

        after = self._snapshot(self.root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, after)

    def _new_repository(self, name: str, slugs: tuple[str, ...]) -> Path:
        root = self.temporary_root / name
        if root.exists():
            raise RuntimeError(f"synthetic repository already exists: {name}")
        for slug in slugs:
            self._write_skill(root, slug)
            self._write_suite(root, slug, self._valid_manifest(slug))
        return root

    @staticmethod
    def _valid_manifest(slug: str) -> dict[str, object]:
        return {
            "schemaVersion": 1,
            "suiteExpectations": {
                "requiredSignals": ["use direct evidence"],
                "prohibitedSignals": ["invent evidence"],
                "repositoryState": "unchanged",
            },
            "cases": [
                {
                    "id": "shared-behavior",
                    "description": "A compact synthetic behavioral case.",
                    "prompt": f"Use ${slug} on the supplied fixture.",
                    "fixture": "basic",
                    "expected": {
                        "requiredSignals": ["inspect the fixture"],
                        "prohibitedSignals": ["claim unobserved behavior"],
                        "repositoryState": "unchanged",
                    },
                }
            ],
            "triggerCases": [
                {
                    "id": "trigger-owned-request",
                    "prompt": f"Use ${slug} for this explicit request.",
                    "expectActivation": True,
                },
                {
                    "id": "near-miss-other-work",
                    "prompt": "Perform an unrelated task.",
                    "expectActivation": False,
                },
            ],
        }

    @staticmethod
    def _safe_commands() -> dict[str, list[dict[str, object]]]:
        return {
            "before": [
                {
                    "purpose": "baseline behavior",
                    "argv": [
                        "python",
                        "-m",
                        "unittest",
                        "discover",
                        "-s",
                        "tests",
                        "-v",
                    ],
                },
                {
                    "purpose": "alternate interpreter contract",
                    "argv": ["python3", "verify.py"],
                },
                {
                    "purpose": "launcher contract",
                    "argv": ["py", "verify.py"],
                },
            ],
            "after": [
                {
                    "purpose": "repository build",
                    "argv": ["dotnet", "build", "Fixture.csproj", "--nologo"],
                }
            ],
        }

    @staticmethod
    def _write_skill(root: Path, slug: str) -> None:
        directory = root / "skills" / slug
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "SKILL.md").write_text(
            "\n".join(
                (
                    "---",
                    f"name: {slug}",
                    "description: Synthetic skill used by validator tests.",
                    "license: MIT",
                    "---",
                    "",
                    f"# {slug}",
                    "",
                )
            ),
            encoding="utf-8",
        )

    @classmethod
    def _write_suite(
        cls, root: Path, slug: str, manifest: dict[str, object]
    ) -> None:
        fixture = root / "evals" / slug / "fixtures" / "basic"
        fixture.mkdir(parents=True, exist_ok=True)
        (fixture / "input.txt").write_text("synthetic fixture\n", encoding="utf-8")
        cls._write_json(root / "evals" / slug / "cases.json", manifest)

    @staticmethod
    def _read_manifest(root: Path, slug: str) -> dict[str, object]:
        return json.loads(
            (root / "evals" / slug / "cases.json").read_text(encoding="utf-8")
        )

    @classmethod
    def _write_manifest(
        cls, root: Path, slug: str, manifest: dict[str, object]
    ) -> None:
        cls._write_json(root / "evals" / slug / "cases.json", manifest)

    @staticmethod
    def _write_json(path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _snapshot(root: Path) -> dict[str, tuple[str, bytes | str]]:
        snapshot: dict[str, tuple[str, bytes | str]] = {}
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                snapshot[relative] = ("link", os.readlink(path))
            elif path.is_dir():
                snapshot[relative] = ("directory", "")
            else:
                snapshot[relative] = ("file", path.read_bytes())
        return snapshot


if __name__ == "__main__":
    unittest.main()
