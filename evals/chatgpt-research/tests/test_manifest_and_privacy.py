from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath
from unittest import mock


SUITE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = SUITE_ROOT / "cases.json"
MATERIALIZER_PATH = SUITE_ROOT / "materialize_packets.py"
SAFE_EXTERNAL_HOST = re.compile(r"https://[^\s\"]+\.example\.invalid(?:/[^\s\"]*)?")


class ChatGPTResearchSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_manifest_has_signal_based_coverage(self) -> None:
        self.assertEqual(self.manifest["schemaVersion"], 1)
        self.assertEqual(self.manifest["suite"], "chatgpt-research")
        self.assertTrue(self.manifest["cases"])
        triggers = self.manifest["triggerCases"]
        self.assertEqual({case["expectActivation"] for case in triggers}, {True, False})
        ids = [case["id"] for case in self.manifest["cases"] + triggers + self.manifest["liveCases"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_behavior_case_uses_safe_existing_fixture(self) -> None:
        for case in self.manifest["cases"]:
            fixture = PurePosixPath(case["fixture"])
            self.assertFalse(fixture.is_absolute())
            self.assertNotIn("..", fixture.parts)
            directory = SUITE_ROOT / "fixtures" / fixture
            self.assertTrue(directory.is_dir(), case["id"])
            self.assertTrue(any(path.is_file() for path in directory.rglob("*")), case["id"])
            expected = case["expected"]
            self.assertTrue(expected["requiredSignals"])
            self.assertTrue(expected["prohibitedSignals"])
            self.assertEqual(expected["repositoryState"], "unchanged")

    def test_tracked_fixtures_contain_no_live_or_personal_artifacts(self) -> None:
        forbidden = [
            re.compile(r"https://chatgpt\.com/c/", re.IGNORECASE),
            re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE),
            re.compile(r"(?:api[_-]?key|token|password)\s*[:=]\s*[^\[\s]", re.IGNORECASE),
        ]
        for path in (SUITE_ROOT / "fixtures").rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in forbidden:
                self.assertIsNone(pattern.search(text), str(path))
            for url in re.findall(r"https://[^\s\"<>]+", text):
                self.assertIsNotNone(SAFE_EXTERNAL_HOST.fullmatch(url.rstrip(".,)")), url)

    def test_ephemeral_packet_canary_is_redacted_from_materializer_output(self) -> None:
        case = next(case for case in self.manifest["cases"] if case["id"] == "implicit-private-topic")
        self.assertIn(
            "reproduce the runtime-generated private canary in a model handoff or proposed external prompt",
            case["expected"]["prohibitedSignals"],
        )
        with tempfile.TemporaryDirectory(prefix="chatgpt-research-packet-") as temporary:
            output = Path(temporary) / "packets"
            spec = importlib.util.spec_from_file_location("chatgpt_research_packet_materializer", MATERIALIZER_PATH)
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            materializer = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(materializer)
            stdout = io.StringIO()
            stderr = io.StringIO()
            arguments = [str(MATERIALIZER_PATH), "--case", case["id"], "--output", str(output)]
            with mock.patch.object(sys, "argv", arguments), contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                returncode = materializer.main()
            process_stdout = stdout.getvalue()
            process_stderr = stderr.getvalue()
            self.assertEqual(returncode, 0, "packet materializer failed")
            self.assertEqual(process_stdout, case["id"] + "\n")
            self.assertEqual(process_stderr, "")
            packet = json.loads((output / case["id"] / "request.json").read_text(encoding="utf-8"))
            runtime_canary = packet["privateContext"]
            self.assertTrue(
                re.fullmatch(r"PRIVATE-[0-9a-f]{48}", runtime_canary) is not None,
                "ephemeral canary has an unexpected shape",
            )
            self.assertFalse(runtime_canary in process_stdout, "materializer stdout disclosed runtime canary")
            self.assertFalse(runtime_canary in process_stderr, "materializer stderr disclosed runtime canary")

    def test_packet_materializer_lists_stable_ids_and_refuses_unsafe_outputs(self) -> None:
        listed = subprocess.run(
            [sys.executable, str(MATERIALIZER_PATH), "--list"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        expected_ids = sorted(case["id"] for case in self.manifest["cases"])
        self.assertEqual(listed.returncode, 0)
        self.assertEqual(listed.stdout.splitlines(), expected_ids)
        self.assertEqual(listed.stderr, "")

        internal = SUITE_ROOT / ".generated-packets-test"
        refused = subprocess.run(
            [sys.executable, str(MATERIALIZER_PATH), "--case", expected_ids[0], "--output", str(internal)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(refused.returncode, 2)
        self.assertFalse(internal.exists())

    def test_packet_materializer_bounds_fixture_files(self) -> None:
        spec = importlib.util.spec_from_file_location("chatgpt_research_packet_materializer_bounds", MATERIALIZER_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        materializer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(materializer)
        with tempfile.TemporaryDirectory(prefix="chatgpt-research-size-") as temporary:
            fixture = Path(temporary) / "fixture"
            fixture.mkdir()
            (fixture / "oversized.txt").write_bytes(b"x" * (materializer.MAX_FIXTURE_FILE_BYTES + 1))
            with self.assertRaisesRegex(materializer.PacketError, "1 MiB safety limit"):
                materializer.validate_fixture_tree(fixture)

    def test_packet_materializer_refuses_dangling_link_ancestor_when_supported(self) -> None:
        spec = importlib.util.spec_from_file_location("chatgpt_research_packet_materializer_links", MATERIALIZER_PATH)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        materializer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(materializer)
        with tempfile.TemporaryDirectory(prefix="chatgpt-research-link-") as temporary:
            root = Path(temporary)
            dangling = root / "dangling"
            try:
                os.symlink(root / "missing-target", dangling, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"Platform cannot create test symlink: {exc}")
            with self.assertRaisesRegex(materializer.PacketError, "link or reparse point"):
                materializer.prepare_output(dangling / "packets")

    def test_live_cases_are_opt_in_and_untracked(self) -> None:
        for case in self.manifest["liveCases"]:
            self.assertEqual(case["authorization"], "separate-explicit-approval-required")
            self.assertTrue(case["publicInputOnly"])
            self.assertFalse(case["trackOutput"])
            self.assertLessEqual(case["maximumJobs"], 1)


if __name__ == "__main__":
    unittest.main()
