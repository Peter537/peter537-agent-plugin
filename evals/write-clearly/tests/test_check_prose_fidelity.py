#!/usr/bin/env python3
"""Black-box tests for the distributed prose-fidelity checker."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path, PurePosixPath


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CHECKER = REPOSITORY_ROOT / "skills" / "write-clearly" / "scripts" / "check_prose_fidelity.py"
CASES = REPOSITORY_ROOT / "evals" / "write-clearly" / "cases.json"
FIXTURES = REPOSITORY_ROOT / "evals" / "write-clearly" / "fixtures"
MAX_INPUT_BYTES = 20 * 1024 * 1024
CASE_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
GIT_ROUTING_VARIABLES = {
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CONFIG_COUNT",
    "GIT_CONFIG_PARAMETERS",
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_TEMPLATE_DIR",
    "GIT_WORK_TREE",
}


class FidelityCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory(prefix="write-clearly-eval-")
        self.temporary_root = Path(self.temporary_directory.name)
        self.canary = f"CANARY-{uuid.uuid4().hex}"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_checker(
        self,
        *arguments: str,
        cwd: Path | None = None,
        environment_updates: dict[str, str] | None = None,
        timeout_seconds: float = 10.0,
    ) -> subprocess.CompletedProcess[str]:
        environment = self.git_environment()
        if environment_updates:
            environment.update(environment_updates)
        return subprocess.run(
            [sys.executable, "-B", str(CHECKER), *arguments],
            cwd=cwd or REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            env=environment,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
        )

    def git_environment(self) -> dict[str, str]:
        environment = os.environ.copy()
        for name in list(environment):
            if name in GIT_ROUTING_VARIABLES or name.startswith(
                ("GIT_CONFIG_KEY_", "GIT_CONFIG_VALUE_")
            ):
                environment.pop(name)
        environment.update(
            {
                "GIT_AUTHOR_DATE": "2000-01-01T00:00:00Z",
                "GIT_AUTHOR_EMAIL": "write-clearly-fixture@example.invalid",
                "GIT_AUTHOR_NAME": "Write Clearly Fixture",
                "GIT_COMMITTER_DATE": "2000-01-01T00:00:00Z",
                "GIT_COMMITTER_EMAIL": "write-clearly-fixture@example.invalid",
                "GIT_COMMITTER_NAME": "Write Clearly Fixture",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_TERMINAL_PROMPT": "0",
            }
        )
        return environment

    def write_pair(
        self,
        before: str | bytes,
        after: str | bytes,
        *,
        suffix: str = ".md",
    ) -> tuple[Path, Path]:
        before_path = self.temporary_root / f"before{suffix}"
        after_path = self.temporary_root / f"after{suffix}"
        before_path.write_bytes(before.encode("utf-8") if isinstance(before, str) else before)
        after_path.write_bytes(after.encode("utf-8") if isinstance(after, str) else after)
        return before_path, after_path

    def run_pair(
        self,
        before: str | bytes,
        after: str | bytes,
        *,
        suffix: str = ".md",
        json_output: bool = True,
        format_name: str | None = None,
    ) -> tuple[subprocess.CompletedProcess[str], dict[str, object] | None]:
        before_path, after_path = self.write_pair(before, after, suffix=suffix)
        arguments = ["--before", str(before_path), "--after", str(after_path)]
        if format_name:
            arguments.extend(["--format", format_name])
        if json_output:
            arguments.append("--json")
        result = self.run_checker(*arguments)
        payload = json.loads(result.stdout) if json_output and result.stdout else None
        return result, payload

    def init_repository(self) -> Path:
        repository = self.temporary_root / "repository"
        repository.mkdir()
        self.run_git(repository, "init", "--quiet")
        self.run_git(repository, "config", "user.name", "Fixture User")
        self.run_git(repository, "config", "user.email", "fixture@example.invalid")
        self.run_git(repository, "config", "core.autocrlf", "false")
        return repository

    def run_git(self, repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [
                "git",
                "-c",
                "commit.gpgSign=false",
                "-c",
                f"core.hooksPath={os.devnull}",
                "-C",
                str(repository),
                *arguments,
            ],
            check=False,
            capture_output=True,
            env=self.git_environment(),
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def commit_all(self, repository: Path, message: str = "fixture") -> None:
        self.run_git(repository, "add", ".")
        self.run_git(repository, "commit", "--quiet", "-m", message)

    def assert_canary_redacted(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertNotIn(self.canary, result.stdout)
        self.assertNotIn(self.canary, result.stderr)

    def test_case_manifest_uses_existing_compact_fixtures(self) -> None:
        payload = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(payload["schemaVersion"], 1)
        suite_expectations = payload["suiteExpectations"]
        for field in ("requiredSignals", "prohibitedSignals"):
            self.assertIsInstance(suite_expectations[field], list)
            self.assertTrue(suite_expectations[field])
            self.assertTrue(all(isinstance(value, str) and value for value in suite_expectations[field]))
        self.assertIsInstance(suite_expectations["repositoryState"], str)
        self.assertTrue(suite_expectations["repositoryState"])

        cases = payload["cases"]
        trigger_cases = payload["triggerCases"]

        case_ids = [case["id"] for case in cases]
        trigger_ids = [case["id"] for case in trigger_cases]
        self.assertEqual(len(case_ids), len(set(case_ids)))
        self.assertEqual(len(trigger_ids), len(set(trigger_ids)))
        self.assertGreaterEqual(len(cases), 12)
        self.assertGreaterEqual(sum(case["expectActivation"] for case in trigger_cases), 5)
        self.assertGreaterEqual(sum(not case["expectActivation"] for case in trigger_cases), 7)

        for case in cases:
            for field in ("id", "description", "prompt", "fixture"):
                self.assertIsInstance(case[field], str)
                self.assertTrue(case[field])
            self.assertRegex(case["id"], CASE_ID_PATTERN)
            fixture_root = FIXTURES / case["fixture"]
            self.assertTrue(fixture_root.is_dir(), case["id"])
            self.assertIsInstance(case["authorizedPaths"], list)
            self.assertTrue(case["authorizedPaths"])
            for relative_path in case["authorizedPaths"]:
                pure_path = PurePosixPath(relative_path)
                self.assertFalse(pure_path.is_absolute(), case["id"])
                self.assertNotIn("..", pure_path.parts, case["id"])
                self.assertTrue((fixture_root / relative_path).is_file(), case["id"])
            expected = case["expected"]
            for field in ("requiredSignals", "prohibitedSignals"):
                self.assertIsInstance(expected[field], list)
                self.assertTrue(expected[field])
                self.assertTrue(all(isinstance(value, str) and value for value in expected[field]))
            self.assertIsInstance(expected["repositoryState"], str)
            self.assertTrue(expected["repositoryState"])
            self.assertNotIn("expectedRewrite", case)

        self.assertEqual(
            {case["fixture"] for case in cases},
            {path.name for path in FIXTURES.iterdir() if path.is_dir()},
        )
        for trigger in trigger_cases:
            self.assertRegex(trigger["id"], CASE_ID_PATTERN)
            self.assertIsInstance(trigger["prompt"], str)
            self.assertTrue(trigger["prompt"])
            self.assertIsInstance(trigger["expectActivation"], bool)

    def test_pair_mode_returns_zero_for_prose_only_change(self) -> None:
        before = "Run `tool verify --strict` for v2.4.0. See https://example.invalid/guide.\n"
        after = "Before deployment, run `tool verify --strict` for v2.4.0. See https://example.invalid/guide.\n"
        result, payload = self.run_pair(before, after)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["coverage"]["input_kind"], "markdown")
        self.assertEqual(payload["coverage"]["level"], "targeted")
        self.assertEqual(payload["coverage"]["warnings"], [])

    def test_human_and_json_results_redact_changed_values(self) -> None:
        before = "No support address is present.\n"
        after = f"See https://example.invalid/{self.canary} for support.\n"

        json_result, payload = self.run_pair(before, after)
        self.assertEqual(json_result.returncode, 1)
        self.assertEqual(payload["status"], "review")
        self.assertIn("url", {finding["category"] for finding in payload["findings"]})
        self.assert_canary_redacted(json_result)

        human_result, _ = self.run_pair(before, after, json_output=False)
        self.assertEqual(human_result.returncode, 1)
        self.assertIn("Values are intentionally redacted", human_result.stdout)
        self.assert_canary_redacted(human_result)

    def test_arbitrary_length_inline_code_span_is_one_protected_literal(self) -> None:
        before = "Use ```alpha `` --old``` for this check.\n"
        after = "Use ```alpha `` --new``` for this check.\n"
        result, payload = self.run_pair(before, after)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["coverage"]["before_categories"]["inline-code"], 1)
        self.assertEqual(payload["coverage"]["after_categories"]["inline-code"], 1)
        self.assertNotIn("cli-flag", payload["coverage"]["before_categories"])
        self.assertEqual({finding["category"] for finding in payload["findings"]}, {"inline-code"})

    def test_escaped_backticks_are_not_inline_code_delimiters(self) -> None:
        before = r"Escaped \`alpha\`; protected ``real ` code``." + "\n"
        after = r"Escaped \`beta\`; protected ``real ` code``." + "\n"
        result, payload = self.run_pair(before, after)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["coverage"]["before_categories"]["inline-code"], 1)
        self.assertEqual(payload["coverage"]["after_categories"]["inline-code"], 1)

    def test_balanced_escaped_and_reference_link_targets_are_protected(self) -> None:
        before = (
            "[Balanced](https://example.invalid/a_(before))\n"
            "[Escaped](https://example.invalid/a\\)before)\n"
            "[Reference][manual]\n\n"
            "[manual]: <https://example.invalid/reference_(before)> \"Manual\"\n"
        )
        after = before.replace("before", "after")
        result, payload = self.run_pair(before, after)

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["coverage"]["before_categories"]["markdown-link-target"], 3)
        self.assertEqual(payload["coverage"]["after_categories"]["markdown-link-target"], 3)
        self.assertNotIn("url", payload["coverage"]["before_categories"])
        self.assertEqual(
            {finding["category"] for finding in payload["findings"]},
            {"markdown-link-target"},
        )

    def test_frontmatter_fence_placeholder_and_counts_are_reported(self) -> None:
        before = (
            "---\nversion: 1.0.0\n---\n\n"
            "Hello {{name}} and {{name}}.\n\n"
            "```python\nprint('before')\n```\n"
        )
        after = (
            "---\nversion: 2.0.0\n---\n\n"
            "Hello {{name}}.\n\n"
            "```python\nprint('after')\n```\n"
        )
        result, payload = self.run_pair(before, after)

        self.assertEqual(result.returncode, 1)
        categories = {finding["category"] for finding in payload["findings"]}
        self.assertEqual(categories, {"fenced-code", "frontmatter", "placeholder"})
        placeholder = next(
            finding for finding in payload["findings"] if finding["category"] == "placeholder"
        )
        self.assertEqual(placeholder["change"], "count-changed")
        self.assertEqual(placeholder["before_count"], 2)
        self.assertEqual(placeholder["after_count"], 1)

    def test_partial_formats_report_redacted_coverage_warnings(self) -> None:
        examples = (
            (".mdx", "# Hello\n\n<Component active={true} />\n", "mdx", "MDX"),
            (".html", '<p data-kind="notice">Hello</p>\n', "html", "HTML"),
            (".py", 'print("hello")\n', "source", "source"),
        )
        for suffix, content, input_kind, warning_term in examples:
            with self.subTest(suffix=suffix):
                result, payload = self.run_pair(content, content, suffix=suffix)
                self.assertEqual(result.returncode, 0, result.stderr)
                coverage = payload["coverage"]
                self.assertEqual(coverage["input_kind"], input_kind)
                self.assertEqual(coverage["level"], "partial")
                self.assertTrue(coverage["warnings"])
                self.assertIn(warning_term.lower(), " ".join(coverage["warnings"]).lower())

        human_result, _ = self.run_pair(
            "# Hello\n\n<Component />\n",
            "# Hello\n\n<Component />\n",
            suffix=".mdx",
            json_output=False,
        )
        self.assertEqual(human_result.returncode, 0)
        self.assertIn("WARNING", human_result.stdout.upper())
        self.assertIn("MDX", human_result.stdout)

    def test_pair_mode_reports_mixed_mdx_and_markdown_coverage(self) -> None:
        before = self.temporary_root / "before.md"
        after = self.temporary_root / "after.mdx"
        before.write_text("# Setup\n\nRun the command.\n", encoding="utf-8")
        after.write_text("# Setup\n\nRun the command.\n", encoding="utf-8")

        result = self.run_checker(
            "--before",
            str(before),
            "--after",
            str(after),
            "--json",
        )
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["coverage"]["input_kind"], "mixed")
        self.assertEqual(payload["coverage"]["level"], "partial")
        warning_text = " ".join(payload["coverage"]["warnings"]).lower()
        self.assertIn("differ", warning_text)
        self.assertIn("mdx", warning_text)

    def test_markdown_with_embedded_html_reports_partial_coverage(self) -> None:
        content = '# Setup\n\n<div data-kind="notice">Run the command.</div>\n'
        result, payload = self.run_pair(content, content)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["coverage"]["input_kind"], "markdown")
        self.assertEqual(payload["coverage"]["level"], "partial")
        self.assertIn("html", " ".join(payload["coverage"]["warnings"]).lower())

        changed_result, changed_payload = self.run_pair(
            content,
            '# Setup\n\n<div data-kind="warning">Run the command.</div>\n',
        )
        self.assertEqual(changed_result.returncode, 1, changed_result.stderr)
        changed_categories = {
            finding["category"] for finding in changed_payload["findings"]
        }
        self.assertTrue({"html-attribute", "html-tag"} & changed_categories)

    def test_complex_localization_marker_only_downgrades_coverage(self) -> None:
        message = '{"files": "{count, plural, one {# file} other {# files}}"}\n'
        result, payload = self.run_pair(message, message, suffix=".json")

        self.assertEqual(result.returncode, 0, result.stderr)
        coverage = payload["coverage"]
        self.assertEqual(coverage["level"], "partial")
        warning_text = " ".join(coverage["warnings"]).lower()
        self.assertTrue("localization" in warning_text or "icu" in warning_text)

    def test_malformed_cli_uses_normal_argparse_error(self) -> None:
        before, _after = self.write_pair("before\n", "after\n")
        result = self.run_checker("--before", str(before))

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("usage:", result.stderr.lower())
        self.assertIn("--before requires --after", result.stderr)

    def test_binary_invalid_utf8_and_oversized_pair_inputs_return_two(self) -> None:
        cases = (
            (b"prefix\x00suffix", b"after", "binary"),
            (b"\xff\xfe\xfa", b"after", "UTF-8"),
            (b"a" * (MAX_INPUT_BYTES + 1), b"after", "20 MiB"),
        )
        for before, after, message_term in cases:
            with self.subTest(message_term=message_term):
                result, payload = self.run_pair(before, after)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(payload["status"], "error")
                self.assertIn(message_term.lower(), payload["message"].lower())

    def test_pair_mode_rejects_non_regular_inputs(self) -> None:
        regular = self.temporary_root / "after.md"
        regular.write_text("After.\n", encoding="utf-8")
        directory = self.temporary_root / "before-directory"
        directory.mkdir()

        result = self.run_checker(
            "--before",
            str(directory),
            "--after",
            str(regular),
            "--json",
        )
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "error")
        self.assertTrue(payload["message"])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO files are unavailable on this host")
    def test_pair_mode_rejects_fifo_without_blocking(self) -> None:
        fifo = self.temporary_root / "before.fifo"
        regular = self.temporary_root / "after.md"
        os.mkfifo(fifo)
        regular.write_text("After.\n", encoding="utf-8")

        result = self.run_checker(
            "--before",
            str(fifo),
            "--after",
            str(regular),
            "--json",
            timeout_seconds=3.0,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "error")
        self.assertIn("regular", payload["message"].lower())

    def test_pair_mode_rejects_symlink_when_supported(self) -> None:
        target = self.temporary_root / "target.md"
        link = self.temporary_root / "before.md"
        after = self.temporary_root / "after.md"
        target.write_text("Target.\n", encoding="utf-8")
        after.write_text("After.\n", encoding="utf-8")
        try:
            os.symlink(target, link)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symbolic links are unavailable: {exc}")

        result = self.run_checker(
            "--before",
            str(link),
            "--after",
            str(after),
            "--json",
        )
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "error")
        self.assertIn("symbolic link", payload["message"].lower())

    def test_adversarial_scan_inputs_fail_safely_within_timeout(self) -> None:
        cases = (
            (self.canary + "[" * 100_000, "unmatched link delimiters", {2}),
            (" ".join(str(index) for index in range(100_000)), "numeric occurrences", {2}),
            (self.canary + "\n" * 250_000, "excessive line count", {2}),
            (self.canary + "<%" * 50_000, "unterminated template markers", {0}),
            (self.canary + "<!--" * 50_000, "unterminated HTML comments", {0}),
            (self.canary + "<!" * 50_000, "unterminated HTML declarations", {0}),
            (self.canary + "<Widget " * 50_000, "unterminated HTML start tags", {0}),
            (
                self.canary + " " + " ".join("`" * length for length in range(1, 2_001)),
                "increasing unmatched backtick runs",
                {0, 2},
            ),
        )
        for content, description, expected_returncodes in cases:
            with self.subTest(description=description):
                before, after = self.write_pair(content, content)
                result = self.run_checker(
                    "--before",
                    str(before),
                    "--after",
                    str(after),
                    "--json",
                    timeout_seconds=5.0,
                )
                payload = json.loads(result.stdout)
                self.assertIn(result.returncode, expected_returncodes)
                if result.returncode == 2:
                    self.assertEqual(payload["status"], "error")
                    self.assertIn("limit", payload["message"].lower())
                else:
                    self.assertEqual(payload["status"], "pass")
                self.assert_canary_redacted(result)

    def test_git_mode_rejects_path_traversal_without_disclosing_file(self) -> None:
        repository = self.init_repository()
        tracked = repository / "guide.md"
        tracked.write_text("Committed text.\n", encoding="utf-8")
        self.commit_all(repository)
        outside = self.temporary_root / "outside.md"
        outside.write_text(self.canary, encoding="utf-8")

        result = self.run_checker(
            "--git-base",
            "HEAD",
            "--path",
            "../outside.md",
            "--json",
            cwd=repository,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "error")
        self.assert_canary_redacted(result)

    def test_git_mode_rejects_symlink_escape_when_supported(self) -> None:
        repository = self.init_repository()
        current = repository / "guide.md"
        current.write_text("Committed text.\n", encoding="utf-8")
        self.commit_all(repository)
        current.unlink()
        outside = self.temporary_root / "symlink-target.md"
        outside.write_text(self.canary, encoding="utf-8")
        try:
            os.symlink(outside, current)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symbolic links are unavailable: {exc}")

        result = self.run_checker(
            "--git-base",
            "HEAD",
            "--path",
            "guide.md",
            "--json",
            cwd=repository,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "error")
        self.assert_canary_redacted(result)

    def test_git_mode_rejects_tracked_symlink_when_supported(self) -> None:
        repository = self.init_repository()
        target = repository / "target.md"
        link = repository / "guide.md"
        target.write_text("Target text.\n", encoding="utf-8")
        try:
            os.symlink("target.md", link)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symbolic links are unavailable: {exc}")
        self.commit_all(repository)

        result = self.run_checker(
            "--git-base",
            "HEAD",
            "--path",
            "guide.md",
            "--json",
            cwd=repository,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "error")

    def test_git_mode_accepts_an_immutable_commit_revision(self) -> None:
        repository = self.init_repository()
        guide = repository / "guide.md"
        guide.write_text("Version 1.0.0.\n", encoding="utf-8")
        self.commit_all(repository, "baseline")
        baseline = self.run_git(repository, "rev-parse", "HEAD").stdout.strip()
        guide.write_text("Version 2.0.0.\n", encoding="utf-8")
        self.commit_all(repository, "current")

        result = self.run_checker(
            "--git-base",
            baseline,
            "--path",
            "guide.md",
            "--json",
            cwd=repository,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(payload["status"], "review")
        self.assertIn("version", {finding["category"] for finding in payload["findings"]})

    def test_git_mode_sizes_and_reads_one_resolved_blob_oid(self) -> None:
        repository = self.init_repository()
        guide = repository / "guide.md"
        guide.write_text("Version 1.0.0.\n", encoding="utf-8")
        self.commit_all(repository, "baseline")
        guide.write_text("Version 2.0.0.\n", encoding="utf-8")
        trace_path = self.temporary_root / "git-trace.jsonl"

        result = self.run_checker(
            "--git-base",
            "HEAD",
            "--path",
            "guide.md",
            "--json",
            cwd=repository,
            environment_updates={"GIT_TRACE2_EVENT": str(trace_path)},
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        if not trace_path.is_file():
            self.skipTest("This Git build did not emit Trace2 event output.")

        command_lines: list[list[str]] = []
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            argv = event.get("argv")
            if isinstance(argv, list) and all(isinstance(value, str) for value in argv):
                command_lines.append(argv)

        revision_commands = [
            argv for argv in command_lines if "rev-parse" in argv and "--verify" in argv
        ]
        self.assertTrue(revision_commands, command_lines)
        self.assertTrue(
            any(any(value.endswith("^{blob}") for value in argv) for argv in revision_commands),
            revision_commands,
        )

        cat_file_commands = [argv for argv in command_lines if "cat-file" in argv]
        sized_oids = [argv[-1] for argv in cat_file_commands if "-s" in argv]
        read_oids = [argv[-1] for argv in cat_file_commands if "-p" in argv]
        self.assertTrue(sized_oids, cat_file_commands)
        self.assertTrue(read_oids, cat_file_commands)
        self.assertRegex(sized_oids[-1], r"\A[0-9a-f]{40,64}\Z")
        self.assertEqual(read_oids[-1], sized_oids[-1])

    def test_git_blob_size_is_checked_before_loading_content(self) -> None:
        repository = self.init_repository()
        guide = repository / "guide.md"
        guide.write_bytes(b"a" * (MAX_INPUT_BYTES + 1))
        self.commit_all(repository)
        guide.write_text("Current text.\n", encoding="utf-8")

        result = self.run_checker(
            "--git-base",
            "HEAD",
            "--path",
            "guide.md",
            "--json",
            cwd=repository,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "error")
        self.assertIn("20 MiB", payload["message"])

    def test_preexisting_dirty_work_requires_pair_baseline(self) -> None:
        repository = self.init_repository()
        guide = repository / "guide.md"
        guide.write_text("See https://example.invalid/original.\n", encoding="utf-8")
        self.commit_all(repository)

        guide.write_text("See https://example.invalid/user-edit.\n", encoding="utf-8")
        pre_task = self.temporary_root / "pre-task.md"
        pre_task.write_bytes(guide.read_bytes())
        guide.write_text(
            "For setup details, see https://example.invalid/user-edit.\n",
            encoding="utf-8",
        )

        pair_result = self.run_checker(
            "--before",
            str(pre_task),
            "--after",
            str(guide),
            "--json",
            cwd=repository,
        )
        git_result = self.run_checker(
            "--git-base",
            "HEAD",
            "--path",
            "guide.md",
            "--json",
            cwd=repository,
        )

        self.assertEqual(pair_result.returncode, 0, pair_result.stderr)
        self.assertEqual(git_result.returncode, 1, git_result.stderr)
        self.assertEqual(json.loads(pair_result.stdout)["status"], "pass")
        self.assertEqual(json.loads(git_result.stdout)["status"], "review")


if __name__ == "__main__":
    unittest.main()
