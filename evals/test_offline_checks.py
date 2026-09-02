"""Tests for the deterministic offline repository-check runner.

The repositories created here are deliberately small and synthetic. They live
under the operating system's temporary directory, perform no network access,
and exercise orchestration and safety boundaries rather than the contents of
the Peter537 Agent Plugin.
"""

from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import textwrap
import unittest
from unittest import mock


RUNNER = Path(__file__).with_name("run_offline_checks.py")


def _load_runner_module() -> object:
    spec = importlib.util.spec_from_file_location("p537_run_offline_checks", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load the offline-check runner module.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RUNNER_MODULE = _load_runner_module()


class OfflineCheckRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="p537-offline-checks-"
        )
        self.temporary_root = Path(self._temporary_directory.name)
        self.root = self._new_repository("fixture")

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    @property
    def recursion_guard(self) -> str:
        return getattr(
            RUNNER_MODULE,
            "RECURSION_GUARD_ENV",
            "P537_OFFLINE_CHECKS_ACTIVE",
        )

    @contextmanager
    def _without_recursion_guard(self):
        previous = os.environ.pop(self.recursion_guard, None)
        try:
            yield
        finally:
            if previous is not None:
                os.environ[self.recursion_guard] = previous

    def run_runner(
        self,
        root: Path | None = None,
        *,
        guard_active: bool = False,
        execute_children: bool = False,
        execute_matching: tuple[str, ...] = (),
        real_git_state: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        selected_root = root or self.root
        if (
            not execute_children
            and not guard_active
            and (selected_root / ".git").is_dir()
        ):
            self.last_child_argv: list[tuple[str, ...]] = []
            tracked = self._git(
                selected_root,
                "ls-files",
                "-z",
                "--cached",
            )
            untracked = self._git(
                selected_root,
                "ls-files",
                "-z",
                "--others",
                "--exclude-standard",
            )

            def simulated_git(rendered: tuple[str, ...]):
                arguments = rendered[1:]
                if arguments == ("rev-parse", "--show-toplevel"):
                    return RUNNER_MODULE.ChildResult(0, str(selected_root) + "\n", "")
                if arguments[:2] == ("status", "--porcelain=v1"):
                    return RUNNER_MODULE.ChildResult(0, "", "")
                if arguments == ("ls-files", "-z", "--cached"):
                    return RUNNER_MODULE.ChildResult(0, tracked, "")
                if arguments == (
                    "ls-files",
                    "-z",
                    "--others",
                    "--exclude-standard",
                ):
                    return RUNNER_MODULE.ChildResult(0, untracked, "")
                if arguments == ("rev-parse", "--verify", "HEAD"):
                    return RUNNER_MODULE.ChildResult(0, "0" * 40 + "\n", "")
                if arguments == ("symbolic-ref", "--quiet", "HEAD"):
                    return RUNNER_MODULE.ChildResult(0, "refs/heads/main\n", "")
                if arguments and arguments[0] == "for-each-ref":
                    return RUNNER_MODULE.ChildResult(
                        0,
                        "refs/heads/main\0" + "0" * 40 + "\0\n",
                        "",
                    )
                if arguments == (
                    "rev-parse",
                    "--path-format=absolute",
                    "--git-path",
                    "index",
                ):
                    return RUNNER_MODULE.ChildResult(
                        0,
                        str(selected_root / ".git" / "index") + "\n",
                        "",
                    )
                if arguments == (
                    "config",
                    "--local",
                    "--null",
                    "--list",
                    "--show-origin",
                ):
                    return RUNNER_MODULE.ChildResult(0, "", "")
                raise AssertionError("The runner attempted an unexpected Git command.")

            def bounded_child(argv, *, cwd, env, timeout):
                rendered = tuple(str(argument) for argument in argv)
                self.last_child_argv.append(rendered)
                should_execute = any(
                    token in argument
                    for token in execute_matching
                    for argument in rendered
                )
                if should_execute or (
                    real_git_state
                    and rendered
                    and rendered[0].casefold() == "git"
                ):
                    return RUNNER_MODULE.run_child(
                        rendered,
                        cwd=cwd,
                        env=env,
                        timeout=timeout,
                    )
                if rendered and rendered[0].casefold() == "git":
                    return simulated_git(rendered)
                return RUNNER_MODULE.ChildResult(0, "", "")

            with self._without_recursion_guard():
                run = RUNNER_MODULE.run_checks(
                    selected_root,
                    child_runner=bounded_child,
                )
            return subprocess.CompletedProcess(
                args=[str(RUNNER), "--root", str(selected_root)],
                returncode=run.exit_code,
                stdout="\n".join(run.lines) + "\n",
                stderr="",
            )

        environment = os.environ.copy()
        if guard_active:
            environment[self.recursion_guard] = "1"
        else:
            environment.pop(self.recursion_guard, None)
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(RUNNER),
                "--root",
                str(selected_root),
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
            timeout=30,
        )

    def assert_passed(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: offline checks", result.stdout)
        self.assertEqual(result.stderr, "")

    def assert_failed(self, result: subprocess.CompletedProcess[str], term: str) -> None:
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL", result.stdout)
        self.assertIn(term.casefold(), result.stdout.casefold())
        self.assertEqual(result.stderr, "")

    def assert_blocked(self, result: subprocess.CompletedProcess[str], term: str) -> None:
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("BLOCKED", result.stdout)
        self.assertIn(term.casefold(), result.stdout.casefold())
        self.assertEqual(result.stderr, "")

    def test_valid_repository_passes_without_mutation(self) -> None:
        before = self._repository_state(self.root)

        result = self.run_runner(execute_children=True)

        self.assert_passed(result)
        self.assertIn("1 suite", result.stdout)
        self.assertIn("1 materializer", result.stdout)
        self.assertIn("1 maintenance test module", result.stdout)
        self.assertIn("1 distributed", result.stdout)
        self.assertIn("NOT_RUN:", result.stdout)
        self.assertEqual(self._repository_state(self.root), before)

    def test_output_is_deterministic_across_identical_runs(self) -> None:
        first = self.run_runner()
        second = self.run_runner()

        self.assert_passed(first)
        self.assert_passed(second)
        self.assertEqual(first.stdout, second.stdout)

    def test_malformed_and_duplicate_json_are_failures(self) -> None:
        malformed = self.root / "metadata.json"
        malformed.write_text('{"broken":', encoding="utf-8")

        malformed_result = self.run_runner()

        self.assert_failed(malformed_result, "json")

        malformed.write_text('{"key": 1, "key": 2}\n', encoding="utf-8")
        duplicate_result = self.run_runner()

        self.assert_failed(duplicate_result, "json")

    def test_supported_yaml_and_frontmatter_pass(self) -> None:
        skill = self.root / "skills" / "alpha" / "SKILL.md"
        skill.write_text(
            """---
name: alpha
description: A bounded scalar description.
license: MIT
metadata:
  maturity: stable
---

# Alpha
""",
            encoding="utf-8",
        )
        agent = self.root / "skills" / "alpha" / "agents" / "openai.yaml"
        agent.write_text(
            """interface:
  display_name: "Alpha"
  short_description: "Synthetic fixture"
  default_prompt: "Use $alpha for this fixture."
policy:
  allow_implicit_invocation: true
""",
            encoding="utf-8",
        )

        result = self.run_runner()

        self.assert_passed(result)

    def test_duplicate_and_unsupported_yaml_are_failures(self) -> None:
        agent = self.root / "skills" / "alpha" / "agents" / "openai.yaml"
        agent.write_text("interface:\n  name: Alpha\n  name: Again\n", encoding="utf-8")

        duplicate_result = self.run_runner()

        self.assert_failed(duplicate_result, "yaml")

        agent.write_text("interface: &shared\n  name: Alpha\n", encoding="utf-8")
        unsupported_result = self.run_runner()

        self.assert_failed(unsupported_result, "yaml")

    def test_malformed_frontmatter_is_a_failure(self) -> None:
        skill = self.root / "skills" / "alpha" / "SKILL.md"
        skill.write_text("---\nname: alpha\n# missing close\n", encoding="utf-8")

        result = self.run_runner()

        self.assert_failed(result, "yaml")

    def test_python_is_compiled_without_creating_bytecode(self) -> None:
        source = self.root / "tools" / "valid.py"
        self._write(source, "value = 1\n")

        valid_result = self.run_runner()

        self.assert_passed(valid_result)
        self.assertFalse(any(self.root.rglob("__pycache__")))

        source.write_text("def broken(:\n    pass\n", encoding="utf-8")
        invalid_result = self.run_runner()

        self.assert_failed(invalid_result, "python")
        self.assertFalse(any(self.root.rglob("__pycache__")))

    def test_valid_markdown_links_images_references_and_fragments_pass(self) -> None:
        self._write(
            self.root / "docs" / "My Guide.md",
            "# Target Heading\n\n## Repeated\n\n## Repeated\n",
        )
        self._write(self.root / "assets" / "pixel.png", "synthetic image bytes")
        (self.root / "README.md").write_text(
            """# Fixture

[Encoded path](docs/My%20Guide.md#target-heading)
[Reference link][guide]
![Local image](assets/pixel.png)
[External](https://example.invalid/not-fetched)

[guide]: <docs/My Guide.md#repeated-1>

`[Ignored inline](missing-inline.md)`

```markdown
[Ignored fenced link](missing-fenced.md)
```
""",
            encoding="utf-8",
        )

        result = self.run_runner()

        self.assert_passed(result)

    def test_literal_and_escaped_link_tokens_are_not_links(self) -> None:
        (self.root / "README.md").write_text(
            r"""# Fixture

The literal token ]( is documentation syntax under discussion.

The escaped token \[label\]\(missing-escaped.md\) is also prose.
""" + "\n",
            encoding="utf-8",
        )

        result = self.run_runner()

        self.assert_passed(result)

    def test_missing_image_reference_definition_is_a_failure(self) -> None:
        (self.root / "README.md").write_text(
            "# Fixture\n\n![Missing image reference][missing-image]\n",
            encoding="utf-8",
        )

        result = self.run_runner()

        self.assert_failed(result, "markdown")

    def test_missing_escaping_mis_cased_and_bad_fragment_links_fail(self) -> None:
        self._write(self.root / "docs" / "Guide.md", "# Existing\n")
        failures = {
            "missing": "[Broken](docs/missing.md)\n",
            "escape": "[Escape](../../outside.md)\n",
            "case": "[Wrong case](docs/guide.md)\n",
            "fragment": "[Wrong fragment](docs/Guide.md#absent)\n",
        }
        for label, content in failures.items():
            with self.subTest(label=label):
                (self.root / "README.md").write_text(content, encoding="utf-8")

                result = self.run_runner()

                self.assert_failed(result, "markdown")

    def test_intentionally_broken_fixture_content_is_excluded(self) -> None:
        fixture = self.root / "evals" / "alpha" / "fixtures" / "broken"
        self._write(fixture / "broken.json", '{"unterminated":')
        self._write(fixture / "broken.py", "def broken(:\n")
        self._write(fixture / "broken.md", "[missing](not-there.md)\n")
        self._write(fixture / "SKILL.md", "---\nname: [unsupported\n---\n")

        result = self.run_runner()

        self.assert_passed(result)

    def test_nonignored_untracked_files_are_checked_but_ignored_files_are_not(self) -> None:
        self._write(self.root / "scratch" / "bad.json", '{"broken":')

        untracked_result = self.run_runner()

        self.assert_failed(untracked_result, "json")

        (self.root / ".gitignore").write_text(
            "__pycache__/\nbin/\nobj/\nnode_modules/\nscratch/\n",
            encoding="utf-8",
        )
        ignored_result = self.run_runner()

        self.assert_passed(ignored_result)

    def test_build_and_cache_directories_are_excluded(self) -> None:
        for directory in ("bin", "obj", "node_modules", "__pycache__"):
            self._write(self.root / directory / "broken.py", "def broken(:\n")

        result = self.run_runner()

        self.assert_passed(result)

    def test_tracked_source_under_build_directories_is_statically_checked(self) -> None:
        ignore_file = self.root / ".gitignore"
        ignore_file.write_text(
            ignore_file.read_text(encoding="utf-8")
            + "build/\nout/\ntarget/\n",
            encoding="utf-8",
        )
        tracked_sources = [
            self.root / directory / "tracked_broken.py"
            for directory in ("build", "bin", "out", "target")
        ]
        for source in tracked_sources:
            self._write(source, "def broken(:\n")
        self._git(self.root, "add", ".gitignore")
        self._git(
            self.root,
            "add",
            "--force",
            *(source.relative_to(self.root).as_posix() for source in tracked_sources),
        )
        self._git(
            self.root,
            "commit",
            "--quiet",
            "-m",
            "Track synthetic generated-source fixtures",
        )

        result = self.run_runner()

        self.assert_failed(result, "python")
        for source in tracked_sources:
            self.assertIn(source.relative_to(self.root).as_posix(), result.stdout)

    def test_manifest_commands_and_live_cases_are_never_executed(self) -> None:
        marker = self.root / "must-not-exist.txt"
        side_effect = self.root / "tools" / "forbidden.py"
        self._write(
            side_effect,
            "from pathlib import Path\nPath('must-not-exist.txt').write_text('bad')\n",
        )
        manifest = self._read_json(self.root / "evals" / "alpha" / "cases.json")
        manifest["cases"][0]["verificationCommands"] = {
            "before": [
                {
                    "purpose": "must remain declarative",
                    "argv": ["powershell", "-Command", "tools/forbidden.py"],
                }
            ],
            "after": [
                {
                    "purpose": "inline execution also remains declarative",
                    "argv": ["python", "-c", "import tools.forbidden"],
                }
            ],
        }
        manifest["liveCases"] = [
            {
                "id": "live-never-run",
                "authorizationRequired": True,
                "requiredSignals": ["must remain opt-in"],
                "argv": ["python", "tools/forbidden.py"],
            }
        ]
        self._write_json(self.root / "evals" / "alpha" / "cases.json", manifest)

        result = self.run_runner()

        self.assert_passed(result)
        self.assertFalse(marker.exists())
        invoked = "\n".join(" ".join(argv) for argv in self.last_child_argv)
        self.assertNotIn("tools/forbidden.py", invoked)
        self.assertNotIn("import tools.forbidden", invoked)

    def test_materializer_list_failure_is_aggregated_without_child_output(self) -> None:
        canary = "CHILD_" + secrets.token_hex(16)
        materializer = self.root / "evals" / "alpha" / "materialize_fixtures.py"
        materializer.write_text(
            f"import sys\nprint({canary!r})\nsys.exit(7)\n",
            encoding="utf-8",
        )

        result = self.run_runner(
            execute_matching=("evals/alpha/materialize_fixtures.py",)
        )

        self.assert_failed(result, "materializer")
        self.assertNotIn(canary, result.stdout + result.stderr)

    def test_suite_without_materializer_is_allowed(self) -> None:
        (self.root / "evals" / "alpha" / "materialize_fixtures.py").unlink()

        result = self.run_runner()

        self.assert_passed(result)
        self.assertIn("0 materializer", result.stdout)

    def test_dual_materializer_aliases_are_rejected(self) -> None:
        existing = self.root / "evals" / "alpha" / "materialize_fixtures.py"
        packet = self.root / "evals" / "alpha" / "materialize_packets.py"
        packet.write_bytes(existing.read_bytes())

        result = self.run_runner()

        self.assert_failed(result, "materializer")
        self.assertIn("both", result.stdout.casefold())

    def test_materializers_are_run_in_suite_order(self) -> None:
        self._add_suite(self.root, "bravo")

        result = self.run_runner()

        self.assert_passed(result)
        alpha = result.stdout.find("alpha")
        bravo = result.stdout.find("bravo")
        self.assertGreaterEqual(alpha, 0, result.stdout)
        self.assertGreater(bravo, alpha, result.stdout)

    def test_root_and_distributed_tests_are_discovered(self) -> None:
        self._write(
            self.root / "evals" / "test_second.py",
            self._unittest_source("RootSecond"),
        )
        self._write(
            self.root / "evals" / "alpha" / "tests" / "test_second.py",
            self._unittest_source("DistributedSecond"),
        )

        result = self.run_runner()

        self.assert_passed(result)
        self.assertIn("2 maintenance test modules", result.stdout)
        self.assertIn("1 distributed", result.stdout)

    def test_nested_git_visible_distributed_test_is_executed(self) -> None:
        self._write(
            self.root
            / "evals"
            / "alpha"
            / "tests"
            / "nested"
            / "test_nested.py",
            self._unittest_source("NestedDistributed", passes=False),
        )

        result = self.run_runner(
            execute_matching=("evals/alpha/tests/nested/test_nested.py",)
        )

        self.assert_failed(result, "distributed-tests/alpha")

    def test_failing_root_and_distributed_tests_are_reported(self) -> None:
        root_test = self.root / "evals" / "test_probe.py"
        root_test.write_text(self._unittest_source("RootProbe", passes=False), encoding="utf-8")

        root_result = self.run_runner(execute_matching=("evals/test_probe.py",))

        self.assert_failed(root_result, "test")

        root_test.write_text(self._unittest_source("RootProbe"), encoding="utf-8")
        distributed = self.root / "evals" / "alpha" / "tests" / "test_probe.py"
        distributed.write_text(
            self._unittest_source("DistributedProbe", passes=False),
            encoding="utf-8",
        )
        distributed_result = self.run_runner(
            execute_matching=("evals/alpha/tests/test_probe.py",)
        )

        self.assert_failed(distributed_result, "test")

    def test_fixture_tests_are_not_discovered(self) -> None:
        self._write(
            self.root
            / "evals"
            / "alpha"
            / "fixtures"
            / "payload"
            / "tests"
            / "test_failure.py",
            self._unittest_source("FixtureFailure", passes=False),
        )

        result = self.run_runner()

        self.assert_passed(result)

    def test_ignored_executable_surfaces_are_never_discovered_or_run(self) -> None:
        ignore_file = self.root / ".gitignore"
        ignore_file.write_text(
            ignore_file.read_text(encoding="utf-8")
            + "evals/test_ignored.py\n"
            + "evals/ignored-suite/\n",
            encoding="utf-8",
        )
        root_marker = self.root / "ignored-root-ran.txt"
        materializer_marker = self.root / "ignored-materializer-ran.txt"
        tests_marker = self.root / "ignored-tests-ran.txt"
        self._write(
            self.root / "evals" / "test_ignored.py",
            "from pathlib import Path\nPath('ignored-root-ran.txt').write_text('bad')\n",
        )
        self._write_json(
            self.root / "evals" / "ignored-suite" / "cases.json",
            {"ignored": True},
        )
        self._write(
            self.root / "evals" / "ignored-suite" / "materialize_fixtures.py",
            """from pathlib import Path
import sys
if '--list' in sys.argv:
    Path('ignored-materializer-ran.txt').write_text('bad', encoding='utf-8')
""",
        )
        self._write(
            self.root / "evals" / "ignored-suite" / "tests" / "test_ignored.py",
            """from pathlib import Path
import unittest


class IgnoredTest(unittest.TestCase):
    def test_must_not_run(self):
        Path('ignored-tests-ran.txt').write_text('bad', encoding='utf-8')
""",
        )

        result = self.run_runner()

        self.assert_passed(result)
        self.assertIn("1 suites", result.stdout)
        self.assertIn("1 materializers", result.stdout)
        self.assertIn("1 maintenance test modules", result.stdout)
        self.assertIn("1 distributed test suites", result.stdout)
        self.assertFalse(root_marker.exists())
        self.assertFalse(materializer_marker.exists())
        self.assertFalse(tests_marker.exists())
        invoked = "\n".join(" ".join(argv) for argv in self.last_child_argv)
        self.assertNotIn("test_ignored.py", invoked)
        self.assertNotIn("ignored-suite", invoked)

    def test_repository_mutation_is_detected_and_never_cleaned(self) -> None:
        materializer = self.root / "evals" / "alpha" / "materialize_fixtures.py"
        materializer.write_text(
            """from pathlib import Path
import sys
if '--list' in sys.argv:
    Path('offline-mutated.txt').write_text('synthetic mutation', encoding='utf-8')
""",
            encoding="utf-8",
        )

        result = self.run_runner(
            execute_matching=("evals/alpha/materialize_fixtures.py",),
            real_git_state=True,
        )

        self.assert_blocked(result, "baseline repository state changed")
        self.assertTrue((self.root / "offline-mutated.txt").exists())

    def test_toctou_rewrite_blocks_later_test_before_launch(self) -> None:
        canary = "TOCTOU_" + secrets.token_hex(20)
        later_test = self.root / "evals" / "test_probe.py"
        marker = self.root / "rewritten-test-ran.txt"
        later_test_launched = False

        def rewrite_before_later_child(argv, *, cwd, env, timeout):
            nonlocal later_test_launched
            rendered = tuple(str(argument) for argument in argv)
            if rendered and rendered[0].casefold() == "git":
                return RUNNER_MODULE.run_child(
                    rendered,
                    cwd=cwd,
                    env=env,
                    timeout=timeout,
                )
            if "evals/alpha/materialize_fixtures.py" in rendered:
                later_test.write_text(
                    "from pathlib import Path\n"
                    f"Path('rewritten-test-ran.txt').write_text({canary!r})\n",
                    encoding="utf-8",
                )
                return RUNNER_MODULE.ChildResult(0, "", "")
            if "evals/test_probe.py" in rendered:
                later_test_launched = True
                marker.write_text("unsafe launch", encoding="utf-8")
            return RUNNER_MODULE.ChildResult(0, "", "")

        with self._without_recursion_guard():
            result = RUNNER_MODULE.run_checks(
                self.root,
                child_runner=rewrite_before_later_child,
            )

        rendered = "\n".join(result.lines)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("BLOCKED: maintenance-test", rendered)
        self.assertIn("baseline repository state changed before child launch", rendered)
        self.assertFalse(later_test_launched)
        self.assertFalse(marker.exists())
        self.assertNotIn(canary, rendered)

    def test_head_mutation_is_detected(self) -> None:
        materializer = self.root / "evals" / "alpha" / "materialize_fixtures.py"
        materializer.write_text(
            """import subprocess
import sys
if '--list' in sys.argv:
    subprocess.run(
        [
            'git',
            '-c', 'user.name=Offline Fixture',
            '-c', 'user.email=offline@example.invalid',
            'commit', '--allow-empty', '--no-gpg-sign', '-m', 'Synthetic mutation',
        ],
        check=True,
        capture_output=True,
    )
""",
            encoding="utf-8",
        )

        result = self.run_runner(
            execute_matching=("evals/alpha/materialize_fixtures.py",),
            real_git_state=True,
        )

        self.assert_blocked(result, "baseline repository state changed")
        self.assertIn("HEAD", result.stdout)

    def test_ref_mutation_is_detected(self) -> None:
        materializer = self.root / "evals" / "alpha" / "materialize_fixtures.py"
        materializer.write_text(
            """import subprocess
import sys
if '--list' in sys.argv:
    subprocess.run(
        ['git', 'update-ref', 'refs/heads/synthetic-side-ref', 'HEAD'],
        check=True,
        capture_output=True,
    )
""",
            encoding="utf-8",
        )

        result = self.run_runner(
            execute_matching=("evals/alpha/materialize_fixtures.py",),
            real_git_state=True,
        )

        self.assert_blocked(result, "baseline repository state changed")
        self.assertIn("ref", result.stdout.casefold())

    def test_index_metadata_mutation_is_detected(self) -> None:
        materializer = self.root / "evals" / "alpha" / "materialize_fixtures.py"
        materializer.write_text(
            """import subprocess
import sys
if '--list' in sys.argv:
    subprocess.run(
        ['git', 'update-index', '--assume-unchanged', 'README.md'],
        check=True,
        capture_output=True,
    )
""",
            encoding="utf-8",
        )

        result = self.run_runner(
            execute_matching=("evals/alpha/materialize_fixtures.py",),
            real_git_state=True,
        )

        self.assert_blocked(result, "baseline repository state changed")
        self.assertIn("index", result.stdout.casefold())

    def test_local_git_config_mutation_is_detected(self) -> None:
        materializer = self.root / "evals" / "alpha" / "materialize_fixtures.py"
        materializer.write_text(
            """import subprocess
import sys
if '--list' in sys.argv:
    subprocess.run(
        ['git', 'config', '--local', 'offline.synthetic-mutation', 'true'],
        check=True,
        capture_output=True,
    )
""",
            encoding="utf-8",
        )

        result = self.run_runner(
            execute_matching=("evals/alpha/materialize_fixtures.py",),
            real_git_state=True,
        )

        self.assert_blocked(result, "baseline repository state changed")
        self.assertIn("config", result.stdout.casefold())

    def test_preexisting_dirty_and_untracked_work_is_preserved(self) -> None:
        readme = self.root / "README.md"
        readme.write_text(readme.read_text(encoding="utf-8") + "\nDirty note.\n", encoding="utf-8")
        self._write(self.root / "notes.txt", "untracked user work\n")
        before = self._repository_state(self.root)

        result = self.run_runner()

        self.assert_passed(result)
        self.assertEqual(self._repository_state(self.root), before)

    def test_runtime_canaries_are_redacted_from_diagnostics(self) -> None:
        canary = "PRIVATE_" + secrets.token_hex(20)
        (self.root / "metadata.json").write_text(
            json.dumps({"privateValue": canary})[:-1],
            encoding="utf-8",
        )

        result = self.run_runner()

        self.assert_failed(result, "json")
        self.assertNotIn(canary, result.stdout + result.stderr)

    def test_private_canary_filename_is_redacted_from_diagnostics(self) -> None:
        canary = "PRIVATE_CANARY_" + secrets.token_hex(20)
        filename = f"private-canary-{canary}.json"
        self._write(self.root / "docs" / filename, '{"broken":')

        result = self.run_runner()

        self.assert_failed(result, "json")
        self.assertNotIn(canary, result.stdout + result.stderr)
        self.assertNotIn(filename, result.stdout + result.stderr)
        self.assertIn("docs/<redacted>", result.stdout)

    def test_control_and_bidi_repository_paths_are_rejected(self) -> None:
        unsafe_paths = (
            "docs/control\x01name.md",
            "docs/bidi\u202ename.md",
            "docs/isolate\u2066name.md",
        )
        for relative in unsafe_paths:
            with self.subTest(relative=ascii(relative)):
                with self.assertRaises(RUNNER_MODULE.InfrastructureError):
                    RUNNER_MODULE._normalize_relative(relative)

    def test_invalid_root_is_an_infrastructure_block(self) -> None:
        missing = self.temporary_root / "missing"

        result = self.run_runner(missing)

        self.assert_blocked(result, "root")

    def test_recursive_invocation_is_refused(self) -> None:
        result = self.run_runner(guard_active=True)

        self.assert_blocked(result, "recursion")

    def test_child_timeout_is_an_infrastructure_block(self) -> None:
        materializer = self.root / "evals" / "alpha" / "materialize_fixtures.py"
        materializer.write_text(
            "import time\ntime.sleep(0.2)\n",
            encoding="utf-8",
        )
        with self._without_recursion_guard():
            result = RUNNER_MODULE.run_checks(self.root, timeout=0.01)

        self.assertEqual(result.exit_code, 2)
        self.assertTrue(any("BLOCKED" in line for line in result.lines))
        self.assertTrue(any("timeout" in line.casefold() for line in result.lines))

    def test_unwritable_temporary_storage_is_an_infrastructure_block(self) -> None:
        with self._without_recursion_guard(), mock.patch.object(
            RUNNER_MODULE.tempfile,
            "TemporaryDirectory",
            side_effect=OSError("synthetic refusal"),
        ):
            result = RUNNER_MODULE.run_checks(self.root)

        rendered = "\n".join(result.lines)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("BLOCKED", rendered)
        self.assertIn("temporary-storage", rendered)

    def test_run_child_uses_direct_argv_closed_stdin_and_no_shell(self) -> None:
        completed = subprocess.CompletedProcess(
            args=["python", "safe.py"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with mock.patch.object(
            RUNNER_MODULE.subprocess, "run", return_value=completed
        ) as process:
            child = RUNNER_MODULE.run_child(
                ("python", "safe.py"),
                cwd=self.root,
                env={"PYTHONHASHSEED": "0"},
                timeout=3,
            )

        self.assertEqual(child.returncode, 0)
        positional, keyword = process.call_args
        self.assertEqual(positional[0], ["python", "safe.py"])
        self.assertIs(keyword["stdin"], subprocess.DEVNULL)
        self.assertIs(keyword["shell"], False)
        self.assertEqual(keyword["timeout"], 3)

    def test_injected_launch_error_is_an_infrastructure_block_and_redacted(self) -> None:
        canary = "LAUNCH_" + secrets.token_hex(16)

        def fail_launch(*args, **kwargs):
            raise RUNNER_MODULE.InfrastructureError(canary)

        with self._without_recursion_guard():
            result = RUNNER_MODULE.run_checks(self.root, child_runner=fail_launch)

        rendered = "\n".join(result.lines)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("BLOCKED", rendered)
        self.assertNotIn(canary, rendered)

    def test_linked_repository_content_is_blocked_when_supported(self) -> None:
        target = self.root / "docs" / "real.md"
        self._write(target, "# Real\n")
        linked = self.root / "docs" / "linked.md"
        try:
            linked.symlink_to(target)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"file links are unavailable: {error.__class__.__name__}")

        result = self.run_runner()

        self.assert_blocked(result, "link")

    def test_linked_materializer_alias_is_blocked_when_supported(self) -> None:
        materializer = self.root / "evals" / "alpha" / "materialize_fixtures.py"
        target = self.root / "tools" / "real_materializer.py"
        self._write(target, materializer.read_text(encoding="utf-8"))
        materializer.unlink()
        try:
            materializer.symlink_to(target)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"file links are unavailable: {error.__class__.__name__}")

        result = self.run_runner(execute_children=True)

        self.assert_blocked(result, "link")

    def test_reparse_materializer_alias_is_blocked(self) -> None:
        original = RUNNER_MODULE.is_link_or_reparse

        def identify_materializer(path: Path) -> bool:
            candidate = Path(path)
            if candidate.name == "materialize_fixtures.py":
                return True
            return original(candidate)

        with self._without_recursion_guard(), mock.patch.object(
            RUNNER_MODULE,
            "is_link_or_reparse",
            side_effect=identify_materializer,
        ):
            result = RUNNER_MODULE.run_checks(self.root)

        rendered = "\n".join(result.lines)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("BLOCKED", rendered)
        self.assertIn("linked-repository-path", rendered)

    def test_disappearing_execution_path_blocks_discovery_without_traceback(self) -> None:
        cases = self.root / "evals" / "alpha" / "cases.json"
        removed = False

        def remove_cases_during_validation(argv, *, cwd, env, timeout):
            nonlocal removed
            if (
                not removed
                and len(argv) >= 3
                and str(argv[0]) == sys.executable
                and str(argv[2]) == "evals/validate_repository_layout.py"
            ):
                cases.unlink()
                removed = True
                return RUNNER_MODULE.ChildResult(0, "", "")
            return RUNNER_MODULE.run_child(
                argv,
                cwd=cwd,
                env=env,
                timeout=timeout,
            )

        with self._without_recursion_guard():
            result = RUNNER_MODULE.run_checks(
                self.root,
                child_runner=remove_cases_during_validation,
            )

        rendered = "\n".join(result.lines)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("BLOCKED: execution-discovery", rendered)
        self.assertNotIn("Traceback", rendered)

    def test_path_case_discovery_error_is_blocked_and_redacted(self) -> None:
        canary = "DISCOVERY_" + secrets.token_hex(16)
        with self._without_recursion_guard(), mock.patch.object(
            RUNNER_MODULE,
            "discover_execution_surface",
            side_effect=RUNNER_MODULE.ContentValidationError(canary),
        ):
            result = RUNNER_MODULE.run_checks(self.root)

        rendered = "\n".join(result.lines)
        self.assertEqual(result.exit_code, 2)
        self.assertIn("BLOCKED: execution-discovery", rendered)
        self.assertNotIn(canary, rendered)
        self.assertNotIn("Traceback", rendered)

    def test_top_level_unexpected_error_is_redacted_without_traceback(self) -> None:
        canary = "TOP_LEVEL_" + secrets.token_hex(16)
        standard_output = io.StringIO()
        standard_error = io.StringIO()
        with self._without_recursion_guard(), mock.patch.object(
            RUNNER_MODULE,
            "run_checks",
            side_effect=RuntimeError(canary),
        ), redirect_stdout(standard_output), redirect_stderr(standard_error):
            exit_code = RUNNER_MODULE.main(["--root", str(self.root)])

        rendered = standard_output.getvalue() + standard_error.getvalue()
        self.assertEqual(exit_code, 2)
        self.assertIn("BLOCKED", rendered)
        self.assertNotIn(canary, rendered)
        self.assertNotIn("Traceback", rendered)

    def test_reparse_detection_is_fail_closed(self) -> None:
        original = RUNNER_MODULE.is_link_or_reparse

        def identify_readme(path: Path) -> bool:
            if Path(path).name == "README.md":
                return True
            return original(path)

        with self._without_recursion_guard(), mock.patch.object(
            RUNNER_MODULE, "is_link_or_reparse", side_effect=identify_readme
        ):
            result = RUNNER_MODULE.run_checks(self.root)

        self.assertEqual(result.exit_code, 2)
        self.assertTrue(any("BLOCKED" in line for line in result.lines))

    def _new_repository(self, name: str) -> Path:
        root = self.temporary_root / name
        root.mkdir(parents=True)
        self._write(root / ".gitignore", "__pycache__/\nbin/\nobj/\nnode_modules/\n")
        self._write(
            root / "README.md",
            "# Fixture\n\n[Skill catalog](docs/skills/README.md)\n",
        )
        self._write_json(
            root / "plugin.json",
            {"name": "Fixture", "version": "0.0.0", "skills": ["./skills/"]},
        )
        self._write_json(
            root / ".codex-plugin" / "plugin.json",
            {"name": "Fixture", "version": "0.0.0", "skills": ["./skills/"]},
        )
        self._write_json(
            root / "skills.sh.json",
            {
                "notGrouped": "bottom",
                "groupings": [
                    {
                        "title": "Fixture group",
                        "description": "Synthetic group.",
                        "skills": ["alpha"],
                    }
                ],
            },
        )
        self._write(
            root / "docs" / "skills" / "README.md",
            "# Skills\n\n[Alpha](../../skills/alpha/SKILL.md)\n",
        )
        self._write(root / "docs" / "verification.md", "# Verification\n")
        self._add_suite(root, "alpha")
        self._write(
            root / "evals" / "validate_repository_layout.py",
            "raise SystemExit(0)\n",
        )
        self._write(
            root / "evals" / "validate_eval_manifests.py",
            "raise SystemExit(0)\n",
        )
        self._write(
            root / "evals" / "test_probe.py",
            self._unittest_source("RootProbe"),
        )
        self._git(root, "init", "--quiet")
        self._git(root, "add", "--all")
        self._git(root, "commit", "--quiet", "-m", "Create synthetic fixture")
        return root

    def _add_suite(self, root: Path, slug: str) -> None:
        skill = root / "skills" / slug
        self._write(
            skill / "SKILL.md",
            f"---\nname: {slug}\ndescription: Synthetic offline fixture.\nlicense: MIT\n---\n\n# {slug.title()}\n",
        )
        self._write(
            skill / "agents" / "openai.yaml",
            f'interface:\n  display_name: "{slug.title()}"\n  short_description: "Synthetic fixture"\n',
        )
        fixture = root / "evals" / slug / "fixtures" / "basic"
        self._write(fixture / "README.md", "Synthetic fixture payload.\n")
        self._write_json(
            root / "evals" / slug / "cases.json",
            {
                "schemaVersion": 1,
                "suite": slug,
                "suiteExpectations": {
                    "requiredSignals": ["bounded evidence"],
                    "prohibitedSignals": ["network access"],
                    "repositoryState": "unchanged",
                },
                "cases": [
                    {
                        "id": "basic-case",
                        "description": "A deterministic synthetic case.",
                        "prompt": "Review the synthetic fixture.",
                        "fixture": "basic",
                        "expected": {
                            "requiredSignals": ["fixture evidence"],
                            "prohibitedSignals": ["invented output"],
                            "repositoryState": "unchanged",
                        },
                    }
                ],
                "triggerCases": [
                    {
                        "id": "positive-trigger",
                        "prompt": f"Use ${slug} for this request.",
                        "expectActivation": True,
                        "expectedOwner": f"${slug}",
                    },
                    {
                        "id": "negative-trigger",
                        "prompt": "Perform unrelated implementation work.",
                        "expectActivation": False,
                        "expectedOwner": "ordinary-implementation",
                    },
                ],
            },
        )
        self._write(
            root / "evals" / slug / "materialize_fixtures.py",
            """import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--list', action='store_true')
arguments = parser.parse_args()
raise SystemExit(0 if arguments.list else 2)
""",
        )
        self._write(
            root / "evals" / slug / "tests" / "test_probe.py",
            self._unittest_source("DistributedProbe"),
        )

    @staticmethod
    def _unittest_source(name: str, *, passes: bool = True) -> str:
        return textwrap.dedent(
            f"""\
            import unittest


            class {name}(unittest.TestCase):
                def test_fixture(self):
                    self.assert{ 'True(True)' if passes else 'True(False)' }


            if __name__ == '__main__':
                unittest.main()
            """
        )

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_json(self, path: Path, value: object) -> None:
        self._write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")

    @staticmethod
    def _read_json(path: Path) -> dict[str, object]:
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def _git(root: Path, *arguments: str) -> str:
        command = ["git"]
        if arguments and arguments[0] == "commit":
            command.extend(
                [
                    "-c",
                    "user.name=Offline Fixture",
                    "-c",
                    "user.email=offline@example.invalid",
                    "-c",
                    "commit.gpgsign=false",
                ]
            )
        command.extend(arguments)
        result = subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env={
                **os.environ,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_TERMINAL_PROMPT": "0",
            },
        )
        if result.returncode != 0:
            raise AssertionError("Could not prepare the synthetic Git repository.")
        return result.stdout

    def _repository_state(self, root: Path) -> tuple[str, tuple[tuple[str, bytes], ...]]:
        status = self._git(root, "status", "--short", "--untracked-files=all")
        files: list[tuple[str, bytes]] = []
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
            if not path.is_file() or ".git" in path.parts:
                continue
            files.append((path.relative_to(root).as_posix(), path.read_bytes()))
        return status, tuple(files)


if __name__ == "__main__":
    unittest.main()
