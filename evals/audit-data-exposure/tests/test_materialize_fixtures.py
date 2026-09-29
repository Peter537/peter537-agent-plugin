from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock

if __package__:
    from .test_scan_repository_data_exposure import (
        REPOSITORY_ROOT, initialize_repository, run_scanner,
    )
else:
    from test_scan_repository_data_exposure import (
        REPOSITORY_ROOT, initialize_repository, run_scanner,
    )


PATH = REPOSITORY_ROOT / "evals/audit-data-exposure/materialize_fixtures.py"
SPEC = importlib.util.spec_from_file_location("exposure_materializer", PATH)
materializer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(materializer)


class MaterializerCanaryTests(unittest.TestCase):
    def test_credential_is_generated_locally_and_scanner_redacts_it(self):
        with tempfile.TemporaryDirectory(prefix="exposure credential fixture ") as directory:
            root = Path(directory) / "repository"
            initialize_repository(root)
            captured = io.StringIO()
            with redirect_stdout(captured), redirect_stderr(captured):
                materializer.inject_private_canary(root, "config/credential.env", "credential")
            raw = (root / "config/credential.env").read_text()
            token = re.search(r'api_key="([0-9a-f]{48})"', raw)
            self.assertTrue(token is not None, "Expected inert runtime credential shape")
            self.assertEqual(captured.getvalue(), "")
            result, payload = run_scanner(root, "--scope", "full")
            self.assertEqual(result.returncode, 0)
            self.assertTrue(any(c["category"] == "credential-assignment" for c in payload["candidates"]))
            self.assertTrue(token.group(1) not in result.stdout + result.stderr, "Credential was disclosed")
            self.assertTrue((root / "config/credential.env").read_text() == raw, "Scanner changed fixture")
            materializer.inject_private_canary(root, "config/second.env", "credential")
            self.assertTrue((root / "config/second.env").read_text() != raw, "Canary was reused")

    def test_existing_record_canary_default_is_preserved(self):
        with tempfile.TemporaryDirectory(prefix="exposure record fixture ") as directory:
            root = Path(directory)
            materializer.inject_private_canary(root, "records.csv")
            text = (root / "records.csv").read_text()
            self.assertTrue(text.startswith("full_name,email,private_path\n"))
            self.assertTrue(re.search(r"private-[0-9a-f]{36}@example\.invalid", text) is not None)

    def test_unsafe_destination_and_unknown_kind_fail_without_echo_or_writes(self):
        with tempfile.TemporaryDirectory(prefix="exposure rejected fixture ") as directory:
            root = Path(directory)
            for path, kind in (("../outside.env", "credential"), (".git/config", "credential"),
                               ("safe.env", "UNTRUSTED_KIND_CANARY")):
                with self.subTest(kind=kind == "credential"):
                    with self.assertRaises(materializer.FixtureError) as caught:
                        materializer.inject_private_canary(root, path, kind)
                    self.assertNotIn("UNTRUSTED_KIND_CANARY", str(caught.exception))
                    self.assertEqual(list(root.iterdir()), [])

    def test_manifest_validates_canary_kind_without_printing_untrusted_value(self):
        manifest = json.loads(materializer.MANIFEST_PATH.read_text())
        case = next(c for c in manifest["cases"] if c["id"] == "maintained-converter-credential")
        for value in ("UNTRUSTED_KIND_CANARY", ["UNTRUSTED_KIND_CANARY"], None):
            case["git"]["canaryKind"] = value
            with mock.patch.object(materializer.json, "loads", return_value=manifest):
                with self.assertRaises(materializer.FixtureError) as caught:
                    materializer.load_manifest()
            self.assertNotIn("UNTRUSTED_KIND_CANARY", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
