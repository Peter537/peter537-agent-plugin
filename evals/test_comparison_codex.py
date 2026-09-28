"""Codex adapter contract tests; no test invokes Codex, a model, or a service."""

from __future__ import annotations

import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

if __package__ in (None, ""):
    # The canonical offline runner invokes root maintenance tests as files.
    # Keep the same module identity used by unittest and the mock seams below.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evals.comparison_codex import AdapterError, CodexAdapter, LOCAL_ONLY_CONFIG, NativeTransport, OFFLINE_GUARD, capture_local_check, package_fingerprint, parse_events


class FakeTransport:
    """Supply declared native-protocol responses, never a subprocess."""

    def __init__(self, workspace, package):
        self.workspace, self.package = workspace, package
        self.calls = []
        self.extra = []
        self.inherited_config = {"apps": None, "hooks": None, "skills": None}
        self.fault = None
        self.events = [{"type": "turn.completed", "usage": {"input_tokens": 31, "output_tokens": 9}}]
        self.result_status = "completed"

    def capture(self, args, workspace, prefix, timeout, *, stdin="", requests=None, validate_response=None):
        self.calls.append((args, workspace, timeout, stdin, requests))
        stdout, stderr = prefix.with_suffix(".stdout"), prefix.with_suffix(".stderr")
        stderr.write_text("private diagnostic canary", encoding="utf-8")
        replies = {}
        if "--version" in args:
            text = "codex-cli 0.158.0-alpha.2.1"
        elif "--help" in args:
            text = "--json --ephemeral --output-last-message" if self.fault != "capability" else "unsupported"
        elif requests is not None:
            text = "native inventory private evidence"
            config = copy.deepcopy(self.inherited_config)
            import tomllib
            for index, argument in enumerate(args):
                if argument == "-c":
                    part = tomllib.loads(args[index + 1])
                    for key, value in part.items():
                        if isinstance(value, dict):
                            if config.get(key) is None:
                                config[key] = {}
                            config.setdefault(key, {}).update(value)
                        else:
                            config[key] = value
            skills = copy.deepcopy(self.extra)
            if self.package is not None:
                skills.append({"name": "example", "path": str(self.package / "SKILL.md"), "enabled": True})
            toggles = (config.get("skills") or {}).get("config") or []
            for item in skills:
                for toggle in toggles:
                    if item["path"] == toggle["path"] and self.fault != "ignored-toggle":
                        item["enabled"] = toggle["enabled"]
            if self.fault == "effective-config":
                config["approval_policy"] = "on-request"
            if self.fault == "missing-local-profile":
                config["features"].pop("hooks", None)
            if self.fault == "enabled-field":
                for item in skills:
                    item.pop("enabled", None)
            replies = {1: {}, 2: {"config": config}, 3: {"requirements": None},
                       4: {"data": [{"cwd": str(workspace), "skills": skills, "errors": []}]},
                       5: {"instructionSources": [str(workspace / "AGENTS.md")]}}
            if self.fault == "instruction-inventory":
                replies[5] = {}
            if validate_response is not None:
                for request in requests:
                    if "id" in request:
                        validate_response(request["id"], replies[request["id"]])
        else:
            text = "\n".join(json.dumps(event) for event in self.events)
            if self.fault == "malformed-event":
                text += "\n{private broken event"
            output_index = args.index("--output-last-message") + 1
            if self.fault != "missing-response":
                Path(args[output_index]).write_text("Synthetic final response.", encoding="utf-8")
        stdout.write_text(text, encoding="utf-8")
        return {"started": True, "status": self.result_status, "exitCode": 0 if self.result_status == "completed" else None,
                "cleanupConfirmed": self.fault != "cleanup", "evidence": [stdout.name, stderr.name],
                "responses": replies, "elapsedSeconds": 0.125}


class CodexAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="p537-codex-contract-")
        self.root = Path(self.temp.name)
        self.workspace = self.root / "target with spaces"
        self.workspace.mkdir()
        (self.workspace / "AGENTS.md").write_text("Preserve unrelated work.", encoding="utf-8")
        self.package = self.workspace / ".agents" / "skills" / "example"
        self.package.mkdir(parents=True)
        (self.package / "SKILL.md").write_text("---\nname: example\ndescription: Example.\n---\nDo the task.\n", encoding="utf-8")
        self.evidence = self.root / "private evidence"
        self.evidence.mkdir()
        self.trial = {"settings": {"executable": "codex", "model": "declared-model", "reasoningEffort": "high",
                                   "sandbox": "workspace-write", "approvalPolicy": "never", "config": {},
                                   "ambientSkills": [], "contextManagement": {}},
                      "prompt": "Review these documents.", "skillName": "example", "authorization": "local trial only"}
        self.fake = FakeTransport(self.workspace, self.package)
        self.adapter = CodexAdapter(self.fake)

    def tearDown(self):
        self.temp.cleanup()

    def preflight(self, package=True):
        return self.adapter.preflight(self.trial, self.workspace, self.package if package else None, self.evidence, 20)

    def execute(self, package=True):
        return self.adapter.execute(self.trial, self.workspace, self.package if package else None, self.evidence, 20)

    def test_complete_fake_trial_preserves_prompt_and_records_observed_metrics(self):
        with mock.patch("subprocess.Popen", side_effect=AssertionError("model launch canary")):
            result = self.preflight()
            self.assertTrue(result["ok"])
            result = self.execute()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["metrics"]["inputTokens"], 31)
        self.assertEqual(result["metrics"]["outputTokens"], 9)
        self.assertIsNone(result["metrics"]["cachedInputTokens"])
        self.assertIsNone(result["metrics"]["observedReadEvents"])
        self.assertEqual(self.fake.calls[-1][3], self.trial["prompt"])
        self.assertNotIn("PASS", str(result))
        self.assertNotIn("private diagnostic canary", str(result))

    def test_no_skill_disables_discovered_evaluated_skill(self):
        self.assertTrue(self.preflight(package=False)["ok"])
        args = self.fake.calls[-1][0]
        self.assertTrue(any('"enabled"=false' in item for item in args))
        self.assertEqual(self.execute(package=False)["status"], "completed")

    def test_duplicate_evaluated_installation_disabled_only_for_process(self):
        self.fake.extra = [{"name": "example", "path": str(self.root / "installed" / "SKILL.md"), "enabled": True}]
        self.assertTrue(self.preflight()["ok"])
        self.assertTrue(any('"enabled"=false' in item for item in self.fake.calls[-1][0]))

    def test_ignored_disable_blocks_isolation(self):
        self.fake.fault = "ignored-toggle"
        result = self.preflight(package=False)
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "skill-isolation-unverified")

    def test_undeclared_ambient_skill_blocks(self):
        self.fake.extra = [{"name": "other", "path": str(self.root / "other" / "SKILL.md"), "enabled": True}]
        self.assertEqual(self.preflight()["reason"], "skill-isolation-unverified")

    def test_declared_ambient_identity_retained_and_rechecked(self):
        ambient = self.root / "ambient"
        ambient.mkdir()
        (ambient / "SKILL.md").write_text("Ambient", encoding="utf-8")
        self.trial["settings"]["ambientSkills"] = [{"name": "other", "path": str(ambient), "sha256": package_fingerprint(ambient)}]
        self.fake.extra = [{"name": "other", "path": str(ambient / "SKILL.md"), "enabled": True}]
        self.assertTrue(self.preflight()["ok"])
        (ambient / "SKILL.md").write_text("Changed", encoding="utf-8")
        self.assertEqual(self.execute()["reason"], "ambient-skill-identity-changed")

    def test_missing_capabilities_effective_settings_cleanup_and_inventory_block(self):
        for fault in ("capability", "effective-config", "cleanup", "enabled-field"):
            with self.subTest(fault=fault):
                self.fake.fault = fault
                self.assertFalse(self.preflight()["ok"])

    def test_package_mutation_and_changed_settings_invalidate_preflight(self):
        self.assertTrue(self.preflight()["ok"])
        (self.package / "SKILL.md").write_text("Changed package", encoding="utf-8")
        self.assertEqual(self.execute()["reason"], "matching-preflight-required")

    def test_preflight_cannot_be_reused_for_duplicate_execution(self):
        self.assertTrue(self.preflight()["ok"])
        self.assertEqual(self.execute()["status"], "completed")
        self.assertEqual(self.execute()["reason"], "matching-preflight-required")

    def test_missing_authorization_unsafe_profile_and_misplaced_package_block(self):
        self.trial["authorization"] = ""
        self.assertEqual(self.preflight()["reason"], "authorization-required")
        self.trial["authorization"] = "local"
        self.trial["settings"]["approvalPolicy"] = "on-request"
        self.assertEqual(self.preflight()["reason"], "unsupported-authority-profile")
        self.trial["settings"]["approvalPolicy"] = "never"
        result = self.adapter.preflight(self.trial, self.workspace, self.root, self.evidence, 1)
        self.assertEqual(result["reason"], "unsupported-package-placement")

    def test_partial_and_malformed_evidence_never_becomes_pass(self):
        self.assertTrue(self.preflight()["ok"])
        self.fake.fault = "malformed-event"
        result = self.execute()
        self.assertTrue(result["started"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "malformed-event-stream")
        self.assertTrue((self.evidence / "execution.stdout").is_file())

    def test_missing_terminal_event_or_response_blocks(self):
        self.assertTrue(self.preflight()["ok"])
        self.fake.events = [{"type": "thread.started"}]
        result = self.execute()
        self.assertEqual(result["reason"], "execution-evidence-incomplete")

    def test_timeout_and_interruption_are_execution_statuses(self):
        for value in ("timeout", "interrupted", "failed"):
            with self.subTest(status=value):
                self.fake.result_status = "completed"
                self.assertTrue(self.preflight()["ok"])
                self.fake.result_status = value
                result = self.execute()
                self.assertEqual(result["status"], value)
                self.assertTrue(result["cleanupConfirmed"])

    def test_offline_guard_prevents_native_launch_at_both_seams(self):
        native = CodexAdapter()
        with mock.patch.dict(os.environ, {OFFLINE_GUARD: "1"}), mock.patch("subprocess.Popen", side_effect=AssertionError("model launch canary")):
            self.assertEqual(native.preflight(self.trial, self.workspace, self.package, self.evidence, 20)["reason"], "offline-model-launch-blocked")
            self.assertEqual(native.execute(self.trial, self.workspace, self.package, self.evidence, 20)["reason"], "offline-model-launch-blocked")
            with self.assertRaisesRegex(AdapterError, "offline-model-launch-blocked"):
                NativeTransport().capture(["codex"], self.workspace, self.evidence / "never", 1)

    def test_exact_repeated_commands_not_inferred_reads_or_approval_counts(self):
        output = self.evidence / "events.jsonl"
        event = {"type": "item.completed", "item": {"type": "command_execution", "command": "read-or-do-anything"}}
        output.write_text("\n".join(json.dumps(item) for item in [event, event, {"type": "turn.completed"}]), encoding="utf-8")
        metrics, complete = parse_events(output)
        self.assertTrue(complete)
        self.assertEqual(metrics["commandEvents"], 2)
        self.assertEqual(metrics["repeatedCommandExecutions"], 1)
        self.assertIsNone(metrics["observedReadEvents"])
        self.assertIsNone(metrics["approvalEvents"])
        self.assertIsNone(metrics["inputTokens"])

    def test_invalid_token_values_rejected(self):
        output = self.evidence / "events.jsonl"
        output.write_text(json.dumps({"type": "turn.completed", "usage": {"input_tokens": True}}), encoding="utf-8")
        with self.assertRaisesRegex(AdapterError, "malformed-token-usage"):
            parse_events(output)

    def test_native_transport_timeout_stops_owned_tree_and_retains_partial_output(self):
        owned = mock.Mock()
        owned.process.communicate.side_effect = subprocess.TimeoutExpired(["codex"], 1)
        owned.stop.return_value = True
        with mock.patch.dict(os.environ, {OFFLINE_GUARD: ""}), mock.patch("evals.comparison_codex._OwnedProcess", return_value=owned), mock.patch("subprocess.Popen", side_effect=AssertionError("model launch canary")):
            result = NativeTransport().capture(["codex"], self.workspace, self.evidence / "partial", 1, stdin="task")
        self.assertEqual(result["status"], "timeout")
        self.assertTrue(result["started"])
        self.assertTrue(result["cleanupConfirmed"])
        owned.stop.assert_called_once()
        self.assertTrue((self.evidence / "partial.stdout").is_file())

    def test_native_transport_cleanup_failure_remains_visible(self):
        owned = mock.Mock()
        owned.process.returncode = 0
        owned.stop.return_value = False
        with mock.patch.dict(os.environ, {OFFLINE_GUARD: ""}), mock.patch("evals.comparison_codex._OwnedProcess", return_value=owned), mock.patch("subprocess.Popen", side_effect=AssertionError("model launch canary")):
            result = NativeTransport().capture(["codex"], self.workspace, self.evidence / "cleanup", 1)
        self.assertFalse(result["cleanupConfirmed"])

    def test_config_override_cannot_weaken_explicit_authority(self):
        self.trial["settings"]["config"] = {"sandbox_mode": "danger-full-access"}
        self.assertEqual(self.preflight()["reason"], "reserved-config-override")

    def test_missing_instruction_inventory_blocks_without_model_turn(self):
        self.fake.fault = "instruction-inventory"
        result = self.preflight()
        self.assertEqual(result["reason"], "ambient-instruction-inventory-unavailable")
        methods = [request["method"] for call in self.fake.calls for request in (call[4] or [])]
        self.assertIn("thread/start", methods)
        self.assertNotIn("turn/start", methods)

    def test_comparison_identity_excludes_only_evaluated_package_toggle(self):
        current = self.preflight()
        none = self.preflight(package=False)
        self.assertTrue(current["ok"])
        self.assertEqual(current["comparisonIdentity"], none["comparisonIdentity"])
        (self.workspace / "AGENTS.md").write_text("Different ambient authority.", encoding="utf-8")
        changed = self.preflight()
        self.assertNotEqual(current["comparisonIdentity"], changed["comparisonIdentity"])

    def test_external_startup_capability_blocks_before_thread_start(self):
        self.trial["settings"]["config"] = {"mcp_servers.remote": {"enabled": True}}
        result = self.preflight()
        self.assertEqual(result["reason"], "unsupported-startup-capability")
        methods = [request["method"] for call in self.fake.calls for request in (call[4] or [])]
        self.assertNotIn("thread/start", methods)

    def test_preflight_cleanup_failure_is_propagated(self):
        self.fake.fault = "cleanup"
        result = self.preflight()
        self.assertFalse(result["cleanupConfirmed"])

    def test_unrelated_skill_disablement_is_preserved_and_part_of_environment_identity(self):
        disabled_path = str(self.root / "disabled ambient" / "SKILL.md")
        self.fake.inherited_config = {"skills": {"config": [{"path": disabled_path, "enabled": False}]}}
        self.fake.extra = [{"name": "other", "path": disabled_path, "enabled": False}]
        result = self.preflight()
        self.assertTrue(result["ok"])
        self.assertTrue(any("disabled ambient" in value for value in self.fake.calls[-1][0]))
        self.fake.inherited_config = {}
        changed = self.preflight()
        self.assertTrue(changed["ok"])
        self.assertNotEqual(result["comparisonIdentity"], changed["comparisonIdentity"])

    def test_instruction_mutation_between_preflight_and_execution_blocks(self):
        self.assertTrue(self.preflight()["ok"])
        (self.workspace / "AGENTS.md").write_text("Changed authority after preflight.", encoding="utf-8")
        self.assertEqual(self.execute()["reason"], "ambient-instruction-identity-changed")

    def test_nonfinite_deadline_blocks_before_transport(self):
        for timeout in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(timeout=timeout):
                result = self.adapter.preflight(self.trial, self.workspace, self.package, self.evidence, timeout)
                self.assertEqual(result["reason"], "preflight-deadline")
        self.assertEqual(self.fake.calls, [])

    def test_reviewed_local_check_remains_available_under_model_launch_guard(self):
        with mock.patch.dict(os.environ, {OFFLINE_GUARD: "1"}):
            result = capture_local_check([sys.executable, "-B", "-c", "print('private local-check canary')"],
                                         self.workspace, self.evidence / "local", 5)
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["cleanupConfirmed"])
        self.assertEqual((self.evidence / "local.stdout").read_text(encoding="utf-8").strip(), "private local-check canary")
        self.assertNotIn("private local-check canary", str(result))

    def test_reviewed_local_check_timeout_terminates_spawned_python_child(self):
        ready, escaped = self.root / "child ready", self.root / "child escaped"
        child = ("from pathlib import Path; import time; "
                 f"Path({str(ready)!r}).write_text('ready'); time.sleep(2); "
                 f"Path({str(escaped)!r}).write_text('unexpected')")
        script = f"import subprocess,sys,time; subprocess.Popen([sys.executable,'-B','-c',{child!r}]); time.sleep(20)"
        with mock.patch.dict(os.environ, {OFFLINE_GUARD: "1"}):
            result = capture_local_check([sys.executable, "-B", "-c", script], self.workspace,
                                         self.evidence / "tree", 1)
        self.assertEqual(result["status"], "timeout")
        self.assertTrue(result["cleanupConfirmed"])
        self.assertTrue(ready.is_file(), "The descendant must start for this teardown test to be meaningful.")
        time.sleep(1.3)
        self.assertFalse(escaped.exists())

    def test_local_only_profile_disables_hooks_and_plugin_mcp_defaults(self):
        self.fake.inherited_config = {"features": {"hooks": True, "plugins": True, "remote_plugin": True,
                                                    "apps": True, "memories": True, "multi_agent": True},
                                      "agents": {"enabled": True}, "web_search": "cached"}
        self.assertTrue(self.preflight()["ok"])
        for key, value in LOCAL_ONLY_CONFIG.items():
            spelling = str(value).lower() if isinstance(value, bool) else json.dumps(value)
            self.assertIn(key + "=" + spelling, self.fake.calls[-1][0])

    def test_unverified_canonical_hook_switch_blocks_before_thread_start(self):
        self.fake.fault = "missing-local-profile"
        self.assertEqual(self.preflight()["reason"], "effective-config-missing")
        methods = [request["method"] for call in self.fake.calls for request in (call[4] or [])]
        self.assertNotIn("thread/start", methods)

    def test_declaration_cannot_reenable_hosted_or_plugin_capabilities(self):
        for key in ("features.remote_plugin", "features.hooks", "features.plugins", "features.apps"):
            with self.subTest(key=key):
                self.trial["settings"]["config"] = {key: True}
                self.assertEqual(self.preflight()["reason"], "unsupported-external-capability")
        self.assertEqual(self.fake.calls, [])

    def test_completed_rpc_does_not_wait_for_persistent_server_exit(self):
        owned = mock.Mock()
        owned.process.stdin = io.BytesIO()
        owned.process.stdout = io.BytesIO(b'{"id":1,"result":{"ready":true}}\n')
        owned.process.returncode = None

        def stop_server():
            owned.process.returncode = -1
            return True

        owned.stop.side_effect = stop_server
        with mock.patch.dict(os.environ, {OFFLINE_GUARD: ""}), mock.patch("evals.comparison_codex._OwnedProcess", return_value=owned), mock.patch("subprocess.Popen", side_effect=AssertionError("model launch canary")):
            result = NativeTransport().capture(["codex", "app-server"], self.workspace,
                                                self.evidence / "persistent", 1,
                                                requests=[{"id": 1, "method": "initialize", "params": {}}])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["exitCode"], -1)
        self.assertEqual(result["completionBasis"], "rpc-responses")
        self.assertTrue(result["cleanupConfirmed"])
        owned.process.wait.assert_not_called()
        owned.stop.assert_called_once()

    def test_native_nullable_app_defaults_are_accepted_only_with_disabled_app_feature(self):
        for apps in (None, {"_default": None}, {"_default": {"enabled": False}}):
            with self.subTest(apps=apps):
                self.fake.inherited_config = {"apps": apps, "hooks": None}
                self.assertTrue(self.preflight()["ok"])
                calls = [request for call in self.fake.calls for request in (call[4] or [])
                         if request["method"] == "config/read"]
                self.assertTrue(all(request["params"]["cwd"] == str(self.workspace) for request in calls))
        self.fake.inherited_config = {"apps": {"_default": {"enabled": True}}}
        self.assertEqual(self.preflight()["reason"], "unsupported-startup-capability")

    def test_native_protocol_failure_diagnostic_omits_sensitive_exception_details(self):
        owned = mock.Mock()
        owned.process.stdin = io.BytesIO()
        owned.process.stdout = io.BytesIO(b'{"id":1,"error":{"message":"private native failure"}}\n')
        owned.process.returncode = None
        owned.stop.return_value = True
        with mock.patch.dict(os.environ, {OFFLINE_GUARD: ""}), mock.patch("evals.comparison_codex._OwnedProcess", return_value=owned), mock.patch("subprocess.Popen", side_effect=AssertionError("model launch canary")):
            result = NativeTransport().capture(["codex", "app-server"], self.workspace,
                                                self.evidence / "protocol-error", 1,
                                                requests=[{"id": 1, "method": "initialize", "params": {}}])
        self.assertEqual(result["reason"], "native-capability-unavailable")
        self.assertNotIn("private native failure", str(result))

    def test_null_absent_and_empty_skill_configuration_have_equal_ambient_identity(self):
        identities = []
        for skills in (None, {}, {"config": None}, {"config": []}):
            with self.subTest(skills=skills):
                self.fake.inherited_config = {"skills": skills}
                current = self.preflight()
                self.assertTrue(current["ok"], current)
                identities.append(current["comparisonIdentity"])
                original_package = self.fake.package
                self.fake.package = None
                none = self.preflight(package=False)
                self.fake.package = original_package
                self.assertTrue(none["ok"], none)
                self.assertEqual(current["comparisonIdentity"], none["comparisonIdentity"])
        self.assertEqual(len(set(identities)), 1)
        self.fake.inherited_config = {}
        self.assertEqual(self.preflight()["comparisonIdentity"], identities[0])

    def test_other_skill_configuration_remains_in_environment_identity(self):
        self.fake.inherited_config = {"skills": {"config": None, "max_context_tokens": 1000}}
        initial = self.preflight()
        self.assertTrue(initial["ok"], initial)
        self.fake.inherited_config["skills"]["max_context_tokens"] = 2000
        changed = self.preflight()
        self.assertTrue(changed["ok"], changed)
        self.assertNotEqual(initial["comparisonIdentity"], changed["comparisonIdentity"])

    def test_process_local_fixture_trust_preserves_other_projects(self):
        other = str(self.root / "another project")
        self.fake.inherited_config = {"projects": {other: {"trust_level": "untrusted", "note": "preserve"}}}
        first = self.preflight()
        self.assertTrue(first["ok"], first)
        overrides = self.fake.calls[-1][0]
        projects = next(value for value in overrides if value.startswith("projects="))
        self.assertIn("another project", projects)
        self.assertIn('"trust_level"="untrusted"', projects)
        self.assertIn('"note"="preserve"', projects)
        self.assertIn('"trust_level"="trusted"', projects)
        result = self.execute()
        self.assertEqual(result["status"], "completed")
        self.assertIn(projects, self.fake.calls[-1][0])
        self.fake.inherited_config["projects"][other]["note"] = "changed ambient setting"
        second = self.preflight()
        self.assertNotEqual(first["comparisonIdentity"], second["comparisonIdentity"])

    def test_explicit_workspace_or_ancestor_distrust_blocks_before_thread_start(self):
        for path in (self.workspace, self.root):
            with self.subTest(path=path):
                self.fake.calls.clear()
                self.fake.inherited_config = {"projects": {str(path): {"trust_level": "untrusted"}}}
                result = self.preflight()
                self.assertEqual(result["reason"], "workspace-explicitly-untrusted")
                methods = [request["method"] for call in self.fake.calls for request in (call[4] or [])]
                self.assertNotIn("thread/start", methods)

    def test_preflight_user_config_mutation_blocks_and_is_not_restored(self):
        config = self.root / "user config.toml"
        config.write_bytes(b"original private settings")
        self.adapter = CodexAdapter(self.fake, user_config_path=config)
        original_capture = self.fake.capture

        def mutate_after_inventory(*args, **kwargs):
            result = original_capture(*args, **kwargs)
            if args[2].name == "inventory-effective":
                config.write_bytes(b"simulated unwanted trust entry")
            return result

        with mock.patch.object(self.fake, "capture", side_effect=mutate_after_inventory):
            result = self.preflight()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "user-config-mutated")
        self.assertFalse(result["userConfigUnchanged"])
        self.assertEqual(config.read_bytes(), b"simulated unwanted trust entry")
        self.assertEqual(self.execute()["reason"], "matching-preflight-required")

    def test_user_config_change_between_preflight_and_execute_prevents_execution(self):
        config = self.root / "user config.toml"
        config.write_bytes(b"original private settings")
        self.adapter = CodexAdapter(self.fake, user_config_path=config)
        self.assertTrue(self.preflight()["ok"])
        count = len(self.fake.calls)
        config.write_bytes(b"separate host change")
        result = self.execute()
        self.assertEqual(result["reason"], "user-config-identity-changed")
        self.assertFalse(result["started"])
        self.assertEqual(len(self.fake.calls), count)

    def test_execution_user_config_mutation_preserves_evidence_and_blocks(self):
        config = self.root / "user config.toml"
        config.write_bytes(b"original private settings")
        self.adapter = CodexAdapter(self.fake, user_config_path=config)
        self.assertTrue(self.preflight()["ok"])
        original_capture = self.fake.capture

        def mutate_after_execute(*args, **kwargs):
            result = original_capture(*args, **kwargs)
            config.write_bytes(b"simulated unwanted runtime setting")
            return result

        with mock.patch.object(self.fake, "capture", side_effect=mutate_after_execute):
            result = self.execute()
        self.assertTrue(result["started"])
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "user-config-mutated")
        self.assertFalse(result["userConfigUnchanged"])
        self.assertIn("execution.stdout", result["evidence"])
        self.assertNotIn("private settings", str(result))

    def test_sanitized_environment_needs_no_home_for_fake_or_offline_blocked_adapter(self):
        with mock.patch.dict(os.environ, {OFFLINE_GUARD: "1", "CODEX_HOME": ""}), mock.patch.object(Path, "home", side_effect=RuntimeError("missing home")), mock.patch("subprocess.Popen", side_effect=AssertionError("model launch canary")):
            fake_adapter = CodexAdapter(self.fake)
            self.assertTrue(fake_adapter.preflight(self.trial, self.workspace, self.package, self.evidence, 20)["ok"])
            native = CodexAdapter()
            result = native.preflight(self.trial, self.workspace, self.package, self.evidence, 20)
            self.assertEqual(result["reason"], "offline-model-launch-blocked")

    def test_missing_native_home_blocks_before_any_process_starts(self):
        with mock.patch.dict(os.environ, {OFFLINE_GUARD: "", "CODEX_HOME": ""}), mock.patch.object(Path, "home", side_effect=RuntimeError("missing home")), mock.patch("subprocess.Popen", side_effect=AssertionError("model launch canary")):
            native = CodexAdapter()
            result = native.preflight(self.trial, self.workspace, self.package, self.evidence, 20)
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "user-config-read-unavailable")


if __name__ == "__main__":
    unittest.main()
