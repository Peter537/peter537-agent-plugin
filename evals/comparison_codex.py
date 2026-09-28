"""Opt-in Codex transport for behavioral comparisons; importing never runs Codex.

The JSONL seam follows https://developers.openai.com/blog/eval-skills . Native
inventory/configuration come from https://learn.chatgpt.com/docs/app-server ;
skill discovery/enablement follow https://learn.chatgpt.com/docs/build-skills .
Protocol compatibility must be established by preflight, not inferred from a
version string. Offline fake-transport tests do not establish real isolation.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import signal
import shutil
import stat
import subprocess
import threading
import time


OFFLINE_GUARD = "P537_OFFLINE_CHECKS_ACTIVE"
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
# Documented local-only switches from the configuration reference. A runtime
# must expose their effective values; unrecognized/omitted fields block instead
# of being assumed disabled. No global config or inherited rules are rewritten.
# https://learn.chatgpt.com/docs/config-file/config-reference
LOCAL_ONLY_CONFIG = {
    "features.hooks": False,
    "features.apps": False,
    "features.browser_use": False,
    "features.computer_use": False,
    "features.image_generation": False,
    "features.memories": False,
    "features.multi_agent": False,
    "features.remote_plugin": False,
    "features.plugins": False,
    "features.skill_mcp_dependency_install": False,
    "agents.enabled": False,
    "web_search": "disabled",
    "sandbox_workspace_write.network_access": False,
}


class AdapterError(Exception):
    """Only fixed diagnostic codes cross the ordinary reporting boundary."""


def package_fingerprint(path: Path) -> str:
    """Hash regular package files without following symlinks or junctions."""
    path = Path(path)
    if path.name == "SKILL.md":
        path = path.parent
    records = []
    for item in [path, *sorted(path.rglob("*"))]:
        info = item.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise AdapterError("linked-package")
        if item.is_file():
            records.append([item.relative_to(path).as_posix(), hashlib.sha256(item.read_bytes()).hexdigest()])
        elif not item.is_dir():
            raise AdapterError("unsupported-package-entry")
    if not (path / "SKILL.md").is_file():
        raise AdapterError("missing-skill-package")
    return hashlib.sha256(json.dumps(records, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def _toml(value):
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int) or isinstance(value, float) and math.isfinite(value):
        return str(value)
    if isinstance(value, list):
        return "[" + ",".join(_toml(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(json.dumps(key) + "=" + _toml(item) for key, item in value.items()) + "}"
    raise AdapterError("unsupported-config-value")


def _lookup(config, dotted):
    for key in dotted.split("."):
        if not isinstance(config, dict) or key not in config:
            raise AdapterError("effective-config-missing")
        config = config[key]
    return config


def _package_path(value):
    path = Path(value)
    return (path.parent if path.name == "SKILL.md" else path).resolve()


class _OwnedProcess:
    """Own the entire child tree: POSIX process group or Windows kill-on-close job.

    Windows starts suspended and assigns its job before resuming, avoiding a
    descendant-spawn race. Failure to establish ownership prevents execution.
    """

    def __init__(self, args, cwd, **streams):
        self.job = None
        self.kernel = None
        self.process = None
        if os.name == "nt":
            from ctypes import wintypes

            class IO_COUNTERS(ctypes.Structure):
                _fields_ = [(name, ctypes.c_ulonglong) for name in (
                    "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                    "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

            class BASIC_LIMITS(ctypes.Structure):
                _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                            ("PerJobUserTimeLimit", ctypes.c_longlong),
                            ("LimitFlags", wintypes.DWORD),
                            ("MinimumWorkingSetSize", ctypes.c_size_t),
                            ("MaximumWorkingSetSize", ctypes.c_size_t),
                            ("ActiveProcessLimit", wintypes.DWORD),
                            ("Affinity", ctypes.c_size_t),
                            ("PriorityClass", wintypes.DWORD),
                            ("SchedulingClass", wintypes.DWORD)]

            class EXTENDED_LIMITS(ctypes.Structure):
                _fields_ = [("BasicLimitInformation", BASIC_LIMITS), ("IoInfo", IO_COUNTERS),
                            ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                            ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
            kernel.CreateJobObjectW.restype = wintypes.HANDLE
            kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
            kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
            kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
            kernel.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            self.kernel, self.job = kernel, kernel.CreateJobObjectW(None, None)
            limits = EXTENDED_LIMITS()
            limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not self.job or not kernel.SetInformationJobObject(self.job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
                self.stop()
                raise AdapterError("process-ownership-unavailable")
            try:
                self.process = subprocess.Popen(args, cwd=cwd, shell=False, creationflags=0x4 | 0x8000000, **streams)
                if not kernel.AssignProcessToJobObject(self.job, wintypes.HANDLE(int(self.process._handle))):
                    raise AdapterError("process-ownership-unavailable")
                resume = ctypes.WinDLL("ntdll").NtResumeProcess
                resume.argtypes = [wintypes.HANDLE]
                resume.restype = ctypes.c_long
                if resume(wintypes.HANDLE(int(self.process._handle))) < 0:
                    raise AdapterError("process-resume-unavailable")
            except BaseException:
                if not self.stop():
                    raise AdapterError("process-cleanup-unconfirmed") from None
                raise
        elif os.name == "posix":
            self.process = subprocess.Popen(args, cwd=cwd, shell=False, start_new_session=True, **streams)
        else:
            raise AdapterError("process-ownership-unavailable")

    def stop(self):
        confirmed = True
        if self.job:
            self.kernel.TerminateJobObject(self.job, 1)
        elif self.process is not None and os.name == "posix":
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                confirmed = False
        if self.process is not None:
            try:
                self.process.kill()
                self.process.wait(timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                confirmed = False
        if self.process is not None and os.name == "posix":
            deadline = time.monotonic() + 5
            while True:
                try:
                    os.killpg(self.process.pid, 0)
                except ProcessLookupError:
                    break
                except OSError:
                    confirmed = False
                    break
                if time.monotonic() >= deadline:
                    confirmed = False
                    break
                time.sleep(0.01)
        if self.job:
            # JOBOBJECT_BASIC_ACCOUNTING_INFORMATION has ActiveProcesses at +40.
            accounting = ctypes.create_string_buffer(48)
            deadline = time.monotonic() + 5
            while True:
                queried = self.kernel.QueryInformationJobObject(self.job, 1, accounting, 48, None)
                active = int.from_bytes(accounting.raw[40:44], "little")
                if queried and active == 0:
                    break
                if time.monotonic() >= deadline:
                    confirmed = False
                    break
                time.sleep(0.01)
            if not self.kernel.CloseHandle(self.job):
                confirmed = False
            self.job = None
        return confirmed


class NativeTransport:
    """The only subprocess seam; tests replace this object entirely."""

    def capture(self, args, workspace, prefix, timeout, *, stdin="", requests=None, validate_response=None):
        if os.environ.get(OFFLINE_GUARD):
            raise AdapterError("offline-model-launch-blocked")
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
            raise AdapterError("invalid-execution-deadline")
        started = time.monotonic()
        owner, reader = None, None
        status, code, responses = "failed", None, {}
        failure_reason = None
        paths = [prefix.with_suffix(".stdout"), prefix.with_suffix(".stderr")]
        cleanup = True
        with paths[0].open("xb") as output, paths[1].open("xb") as errors:
            try:
                if requests is None:
                    owner = _OwnedProcess(args, workspace, stdin=subprocess.PIPE, stdout=output, stderr=errors)
                    owner.process.communicate(stdin.encode(), timeout=timeout)
                    code = owner.process.returncode
                    status = "completed" if code == 0 else "failed"
                else:
                    owner = _OwnedProcess(args, workspace, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors)
                    lines = queue.Queue()

                    def read_lines():
                        while True:
                            line = owner.process.stdout.readline(MAX_OUTPUT_BYTES + 1)
                            if not line:
                                lines.put(None)
                                return
                            output.write(line)
                            output.flush()
                            lines.put(line)
                            if len(line) > MAX_OUTPUT_BYTES:
                                return

                    reader = threading.Thread(target=read_lines, daemon=True)
                    reader.start()
                    for request in requests:
                        owner.process.stdin.write((json.dumps(request) + "\n").encode())
                        owner.process.stdin.flush()
                        if "id" not in request:
                            continue
                        while True:
                            remaining = timeout - (time.monotonic() - started)
                            if remaining <= 0:
                                raise subprocess.TimeoutExpired(args, timeout)
                            try:
                                line = lines.get(timeout=remaining)
                            except queue.Empty:
                                raise subprocess.TimeoutExpired(args, timeout) from None
                            if line is None or len(line) > MAX_OUTPUT_BYTES:
                                raise AdapterError("native-protocol-incomplete")
                            try:
                                response = json.loads(line)
                            except (ValueError, UnicodeError):
                                raise AdapterError("native-protocol-invalid") from None
                            if not isinstance(response, dict):
                                raise AdapterError("native-protocol-invalid")
                            if response.get("id") == request["id"]:
                                if "error" in response or "result" not in response:
                                    raise AdapterError("native-capability-unavailable")
                                responses[request["id"]] = response["result"]
                                if validate_response is not None:
                                    validate_response(request["id"], response["result"])
                                break
                    owner.process.stdin.close()
                    # App-server is persistent. Validated responses complete
                    # this read-only RPC session; owned teardown below is
                    # intentional, not a failed request or execution timeout.
                    status = "completed"
            except subprocess.TimeoutExpired:
                status = "timeout"
            except KeyboardInterrupt:
                status = "interrupted"
            except (OSError, AdapterError, KeyError, TypeError, ValueError, AttributeError) as error:
                status = "failed"
                failure_reason = str(error) if isinstance(error, AdapterError) else "native-protocol-unavailable"
                if isinstance(error, AdapterError) and str(error) == "process-cleanup-unconfirmed":
                    cleanup = False
            finally:
                if owner is not None:
                    cleanup = owner.stop()
                    if requests is not None:
                        code = owner.process.returncode
                if reader is not None:
                    reader.join(timeout=5)
                    cleanup = cleanup and not reader.is_alive()
                    if not reader.is_alive():
                        owner.process.stdout.close()
        result = {"started": owner is not None, "status": status, "exitCode": code,
                "cleanupConfirmed": cleanup, "responses": responses,
                "evidence": [path.name for path in paths], "elapsedSeconds": time.monotonic() - started,
                "completionBasis": "rpc-responses" if requests is not None else "process-exit"}
        if failure_reason is not None:
            result["reason"] = failure_reason
        return result


def capture_local_check(argv, cwd, prefix, timeout):
    """Capture one reviewed local command with owned-tree teardown, without models.

    Selection/authorization belongs to the caller. This utility deliberately
    does not interpret shell strings, execute manifest commands implicitly, or
    print captured output. The model-launch guard does not forbid offline
    fixture checks such as Python unittest. It is not a network sandbox.
    """
    if (not isinstance(argv, list) or not argv or any(not isinstance(item, str) or "\x00" in item for item in argv)
            or type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0):
        raise AdapterError("invalid-local-check")
    start = time.monotonic()
    owner = None
    status, code, cleanup = "failed", None, True
    paths = [Path(prefix).with_suffix(".stdout"), Path(prefix).with_suffix(".stderr")]
    try:
        with paths[0].open("xb") as output, paths[1].open("xb") as errors:
            try:
                owner = _OwnedProcess(argv, cwd, stdin=subprocess.DEVNULL, stdout=output, stderr=errors)
                code = owner.process.wait(timeout=timeout)
                status = "completed" if code == 0 else "failed"
            except subprocess.TimeoutExpired:
                status = "timeout"
            except KeyboardInterrupt:
                status = "interrupted"
            except (OSError, AdapterError) as error:
                if isinstance(error, AdapterError) and str(error) == "process-cleanup-unconfirmed":
                    cleanup = False
            finally:
                if owner is not None:
                    cleanup = owner.stop()
    except OSError:
        status = "failed"
    return {"started": owner is not None, "status": status, "exitCode": code,
            "cleanupConfirmed": cleanup, "evidence": [path.name for path in paths if path.is_file()],
            "elapsedSeconds": time.monotonic() - start}


def parse_events(path):
    """Return measured telemetry only; shell commands do not prove file reads."""
    metrics = {"inputTokens": None, "outputTokens": None, "cachedInputTokens": None,
               "commandEvents": 0, "repeatedCommandExecutions": 0,
               "observedReadEvents": None, "approvalEvents": None, "cost": None}
    if path.stat().st_size > MAX_OUTPUT_BYTES:
        raise AdapterError("event-output-limit")
    seen, completed = set(), False
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except (ValueError, UnicodeError):
                raise AdapterError("malformed-event-stream") from None
            if not isinstance(event, dict) or not isinstance(event.get("type"), str):
                raise AdapterError("malformed-event-stream")
            if event["type"] == "item.completed":
                item = event.get("item")
                if not isinstance(item, dict):
                    raise AdapterError("malformed-event-stream")
                if item.get("type") == "command_execution":
                    command = item.get("command")
                    if not isinstance(command, str):
                        raise AdapterError("malformed-event-stream")
                    metrics["commandEvents"] += 1
                    metrics["repeatedCommandExecutions"] += int(command in seen)
                    seen.add(command)
            if event["type"] == "turn.completed":
                if completed:
                    raise AdapterError("multiple-turn-results")
                completed = True
                usage = event.get("usage", {})
                if not isinstance(usage, dict):
                    raise AdapterError("malformed-event-stream")
                for native, public in (("input_tokens", "inputTokens"), ("output_tokens", "outputTokens"),
                                       ("cached_input_tokens", "cachedInputTokens")):
                    value = usage.get(native)
                    if value is not None and (type(value) is not int or value < 0):
                        raise AdapterError("malformed-token-usage")
                    metrics[public] = value
    return metrics, completed


class CodexAdapter:
    name = "codex-exec"
    simulated = False

    def __init__(self, transport=None, *, user_config_path=None):
        self.transport = transport if transport is not None else NativeTransport()
        self._ready = {}
        self._preflight_cleanup = True
        self._guard_user_config = isinstance(self.transport, NativeTransport) or user_config_path is not None
        self._user_config_path = Path(user_config_path) if user_config_path is not None else None

    def _user_config_state(self):
        if not self._guard_user_config:
            return None
        try:
            if self._user_config_path is None:
                configured_home = os.environ.get("CODEX_HOME")
                config_home = Path(configured_home) if configured_home else Path.home() / ".codex"
                self._user_config_path = config_home / "config.toml"
            content = self._user_config_path.read_bytes()
        except FileNotFoundError:
            return {"exists": False}
        except (OSError, RuntimeError):
            raise AdapterError("user-config-read-unavailable") from None
        return {"exists": True, "sha256": hashlib.sha256(content).hexdigest()}

    def _workspace_projects(self, inherited, workspace):
        projects = {} if inherited is None else json.loads(json.dumps(inherited))
        if not isinstance(projects, dict):
            raise AdapterError("project-trust-unavailable")
        target = workspace.resolve()
        target_key = str(target)
        for key, entry in projects.items():
            if not isinstance(key, str) or not isinstance(entry, dict):
                raise AdapterError("project-trust-unavailable")
            project = Path(key).resolve()
            if (project == target or project in target.parents) and entry.get("trust_level") == "untrusted":
                raise AdapterError("workspace-explicitly-untrusted")
            if project == target:
                target_key = key
        current = projects.setdefault(target_key, {})
        current["trust_level"] = "trusted"
        return projects, target_key

    def _settings(self, trial, workspace, package):
        settings = trial["settings"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", trial["skillName"]):
            raise AdapterError("invalid-skill-name")
        if not isinstance(trial.get("authorization"), str) or not trial["authorization"].strip():
            raise AdapterError("authorization-required")
        if settings.get("approvalPolicy") != "never" or settings.get("sandbox") not in ("workspace-write", "read-only"):
            raise AdapterError("unsupported-authority-profile")
        for key in ("model", "reasoningEffort", "executable"):
            if not isinstance(settings.get(key), str) or not settings[key].strip():
                raise AdapterError("missing-model-settings")
        if not isinstance(settings.get("ambientSkills"), list) or not isinstance(settings.get("contextManagement"), dict):
            raise AdapterError("missing-context-settings")
        config = dict(settings.get("config", {}))
        config.update(settings["contextManagement"])
        reserved = {"model", "model_reasoning_effort", "approval_policy", "sandbox_mode", "skills.config"}
        if reserved.intersection(config) or any(not re.fullmatch(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*", key) for key in config):
            raise AdapterError("reserved-config-override")
        if any(key in config and config[key] != value for key, value in LOCAL_ONLY_CONFIG.items()):
            raise AdapterError("unsupported-external-capability")
        config.update(LOCAL_ONLY_CONFIG)
        config.update(model=settings["model"], model_reasoning_effort=settings["reasoningEffort"],
                      approval_policy="never", sandbox_mode=settings["sandbox"])
        if package is not None:
            expected = workspace / ".agents" / "skills" / trial["skillName"]
            if package.resolve() != expected.resolve():
                raise AdapterError("unsupported-package-placement")
            package_fingerprint(package)
        ambient = {}
        for skill in settings["ambientSkills"]:
            path = _package_path(skill["path"])
            if skill["name"] == trial["skillName"] or str(path) in ambient:
                raise AdapterError("ambiguous-ambient-skills")
            if package_fingerprint(path) != skill["sha256"]:
                raise AdapterError("ambient-skill-identity-changed")
            ambient[str(path)] = skill["name"]
        return settings["executable"], config, ambient

    def _rpc(self, executable, config, workspace, evidence_dir, suffix, timeout, *, start_thread=False):
        overrides = []
        for key, value in sorted(config.items()):
            overrides += ["-c", key + "=" + _toml(value)]
        requests = [
            {"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "p537-evals", "version": "1"}, "capabilities": {"experimentalApi": True}}},
            {"method": "initialized", "params": {}},
            {"id": 2, "method": "config/read", "params": {"includeLayers": True, "cwd": str(workspace)}},
            {"id": 3, "method": "configRequirements/read", "params": {}},
            {"id": 4, "method": "skills/list", "params": {"cwds": [str(workspace)], "forceReload": True}},
        ]
        if start_thread:
            requests.append({"id": 5, "method": "thread/start", "params": {
                "cwd": str(workspace), "model": config["model"], "ephemeral": True,
                "approvalPolicy": "never", "sandbox": config["sandbox_mode"],
            }})

        def validate_response(identifier, response):
            if identifier != 2:
                return
            effective = response["config"]
            for key, value in config.items():
                if _lookup(effective, key) != value:
                    raise AdapterError("effective-config-mismatch")
            # v1 deliberately supports no external servers/apps/hooks. This
            # check occurs before thread/start can initialize those services.
            for key in ("mcp_servers", "apps"):
                capabilities = effective.get(key, {})
                # Native Config.apps and AppsConfig._default are nullable.
                # The independently verified features.apps=false remains the
                # authority for treating null app defaults as unavailable.
                if key == "apps" and capabilities is None:
                    continue
                if not isinstance(capabilities, dict) or any(
                    (not isinstance(item, dict) or item.get("enabled", True))
                    for item in capabilities.values()
                    if not (key == "apps" and item is None)
                ):
                    raise AdapterError("unsupported-startup-capability")
            if effective.get("hooks") or effective.get("features", {}).get("codex_hooks", False):
                raise AdapterError("unsupported-startup-capability")

        result = self.transport.capture([executable, *overrides, "app-server"], workspace,
                                        evidence_dir / suffix, timeout, requests=requests,
                                        validate_response=validate_response)
        self._preflight_cleanup = self._preflight_cleanup and result["cleanupConfirmed"]
        if result["status"] != "completed" or not result["cleanupConfirmed"]:
            safe_reasons = {"native-protocol-incomplete", "native-protocol-invalid", "native-capability-unavailable",
                            "effective-config-missing", "effective-config-mismatch", "unsupported-startup-capability",
                            "process-cleanup-unconfirmed"}
            reason = result.get("reason")
            raise AdapterError(reason if reason in safe_reasons else "native-inventory-unavailable")
        responses = result["responses"]
        effective = responses[2]["config"]
        for key, value in config.items():
            if _lookup(effective, key) != value:
                raise AdapterError("effective-config-mismatch")
        if not isinstance(responses[3], dict) or "requirements" not in responses[3]:
            raise AdapterError("requirements-unavailable")
        rows = responses[4]["data"]
        if len(rows) != 1 or Path(rows[0]["cwd"]).resolve() != workspace.resolve() or rows[0].get("errors"):
            raise AdapterError("skill-inventory-incomplete")
        skills = rows[0]["skills"]
        if not isinstance(skills, list) or any(not isinstance(item, dict) or type(item.get("enabled")) is not bool for item in skills):
            raise AdapterError("skill-enablement-unavailable")
        return skills, overrides, result, responses

    def _identity(self, trial, workspace, package):
        return hashlib.sha256(json.dumps({"trial": trial, "workspace": str(workspace.resolve()),
                                          "package": package_fingerprint(package) if package else None},
                                         sort_keys=True).encode()).hexdigest()

    def preflight(self, trial, workspace, package, evidence_dir, timeout):
        if isinstance(self.transport, NativeTransport) and os.environ.get(OFFLINE_GUARD):
            return {"ok": False, "reason": "offline-model-launch-blocked", "cleanupConfirmed": True}
        try:
            before = self._user_config_state()
        except AdapterError as error:
            return {"ok": False, "reason": str(error), "cleanupConfirmed": True}
        result = self._preflight_impl(trial, workspace, package, evidence_dir, timeout)
        try:
            after = self._user_config_state()
        except AdapterError as error:
            self._ready.clear()
            return {**result, "ok": False, "reason": str(error), "userConfigUnchanged": False}
        if before != after:
            self._ready.clear()
            return {**result, "ok": False, "reason": "user-config-mutated", "userConfigUnchanged": False}
        if result["ok"]:
            self._ready[self._identity(trial, workspace, package)]["userConfigState"] = before
        result["userConfigUnchanged"] = True if self._guard_user_config else None
        return result

    def _preflight_impl(self, trial, workspace, package, evidence_dir, timeout):
        if isinstance(self.transport, NativeTransport) and os.environ.get(OFFLINE_GUARD):
            return {"ok": False, "reason": "offline-model-launch-blocked", "cleanupConfirmed": True}
        started, evidence = time.monotonic(), []
        self._preflight_cleanup = True
        comparison_identity = None
        try:
            executable, config, ambient = self._settings(trial, workspace, package)
            executable_identity = {"kind": "simulated-transport"}
            if isinstance(self.transport, NativeTransport):
                located = shutil.which(executable)
                if not located or Path(located).suffix.lower() in (".cmd", ".bat", ".ps1"):
                    raise AdapterError("native-executable-unavailable")
                executable = str(Path(located).resolve())
                executable_identity = {"sha256": hashlib.sha256(Path(executable).read_bytes()).hexdigest()}
            if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
                raise AdapterError("preflight-deadline")
            def remaining():
                value = timeout - (time.monotonic() - started)
                if value <= 0:
                    raise AdapterError("preflight-deadline")
                return value
            for suffix, args in (("version", ["--version"]), ("capabilities", ["exec", "--help"])):
                result = self.transport.capture([executable, *args], workspace, evidence_dir / suffix, remaining())
                self._preflight_cleanup = self._preflight_cleanup and result["cleanupConfirmed"]
                evidence.extend(result["evidence"])
                if result["status"] != "completed" or not result["cleanupConfirmed"]:
                    raise AdapterError("cli-capability-unavailable")
                output = (evidence_dir / result["evidence"][0]).read_text(encoding="utf-8")
                if suffix == "version" and not re.search(r"codex-cli \d+\.\d+", output):
                    raise AdapterError("cli-version-unavailable")
                if suffix == "version":
                    executable_identity["version"] = output.strip()
                if suffix == "capabilities" and any(flag not in output for flag in ("--json", "--ephemeral", "--output-last-message")):
                    raise AdapterError("cli-capability-unavailable")
            inventory, _, result, initial = self._rpc(executable, config, workspace, evidence_dir, "inventory-initial", remaining())
            evidence.extend(result["evidence"])
            # Supply fresh fixture trust only to this process, retaining every
            # inherited project entry and refusing an explicit relevant denial.
            # This avoids native thread/start persisting trust opportunistically.
            # The surrounding byte guard verifies that property for each run.
            # https://learn.chatgpt.com/docs/config-file/config-advanced
            projects, generated_project_key = self._workspace_projects(initial[2]["config"].get("projects"), workspace)
            config["projects"] = projects
            evaluated = [item for item in inventory if item.get("name") == trial["skillName"]]
            chosen = str(package.resolve()) if package else None
            toggles = [{"path": item["path"], "enabled": str(_package_path(item["path"])) == chosen} for item in evaluated]
            if chosen and sum(str(_package_path(item["path"])) == chosen for item in evaluated) != 1:
                raise AdapterError("selected-package-not-discovered")
            if toggles:
                inherited_settings = initial[2]["config"].get("skills")
                if inherited_settings is None:
                    inherited_settings = {}
                if not isinstance(inherited_settings, dict):
                    raise AdapterError("skill-enablement-unavailable")
                inherited = inherited_settings.get("config")
                if inherited is None:
                    inherited = []
                if not isinstance(inherited, list) or any(
                    not isinstance(item, dict) or not isinstance(item.get("path"), str)
                    or type(item.get("enabled")) is not bool for item in inherited
                ):
                    raise AdapterError("skill-enablement-unavailable")
                combined = {str(_package_path(item["path"])): item for item in inherited}
                if len(combined) != len(inherited):
                    raise AdapterError("ambiguous-skill-configuration")
                combined.update({str(_package_path(item["path"])): item for item in toggles})
                config["skills.config"] = list(combined.values())
            inventory, overrides, result, native = self._rpc(executable, config, workspace, evidence_dir, "inventory-effective", remaining(), start_thread=True)
            evidence.extend(result["evidence"])
            actual = {}
            for item in inventory:
                if item["enabled"]:
                    key = str(_package_path(item["path"]))
                    if key in actual:
                        raise AdapterError("duplicate-skill-exposure")
                    actual[key] = item["name"]
            expected = dict(ambient)
            if chosen:
                expected[chosen] = trial["skillName"]
            if actual != expected:
                raise AdapterError("skill-isolation-unverified")
            # Exclude only evaluated-package enablement, the intended treatment.
            # Paths/trust settings and every other effective setting remain in the
            # identity; do not normalize away real host/environment differences.
            effective = json.loads(json.dumps(native[2]["config"]))
            if isinstance(effective.get("projects"), dict) and generated_project_key in effective["projects"]:
                generated = effective["projects"].pop(generated_project_key)
                effective["projects"]["<workspace>"] = generated
            # Native unset optional skill configuration may be null, absent,
            # or empty. Normalize only that absence; preserve every meaningful
            # setting and every unrelated explicit enablement rule.
            if effective.get("skills") is None:
                effective.pop("skills", None)
            if isinstance(effective.get("skills"), dict):
                evaluated_paths = {str(_package_path(item["path"])) for item in evaluated}
                rules = effective["skills"].get("config")
                if rules is None:
                    rules = []
                retained = [item for item in rules
                            if str(_package_path(item["path"])) not in evaluated_paths]
                if retained:
                    effective["skills"]["config"] = retained
                else:
                    effective["skills"].pop("config", None)
                if not effective["skills"]:
                    effective.pop("skills")
            sources = native[5].get("instructionSources")
            if not isinstance(sources, list) or any(not isinstance(item, str) for item in sources):
                raise AdapterError("ambient-instruction-inventory-unavailable")
            source_identity, source_files = [], {}
            seen_sources = set()
            for source in sources:
                path = Path(source)
                if not path.is_absolute() or not path.is_file():
                    raise AdapterError("ambient-instruction-source-unavailable")
                for ancestor in [path, *path.parents]:
                    info = ancestor.lstat()
                    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                        raise AdapterError("linked-instruction-source")
                resolved = path.resolve()
                if str(resolved) in seen_sources:
                    raise AdapterError("duplicate-instruction-source")
                seen_sources.add(str(resolved))
                try:
                    normalized = "<workspace>/" + resolved.relative_to(workspace.resolve()).as_posix()
                except ValueError:
                    normalized = str(resolved)
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                source_identity.append({"path": normalized, "sha256": digest})
                source_files[str(resolved)] = digest
            comparison_identity = hashlib.sha256(json.dumps({
                "config": effective, "requirements": native[3]["requirements"],
                "executable": executable_identity, "ambientSkills": trial["settings"]["ambientSkills"],
                "instructionSources": source_identity,
            }, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            identity = self._identity(trial, workspace, package)
            self._ready[identity] = {"args": [executable, *overrides], "instructionFiles": source_files,
                                     "executableIdentity": executable_identity}
            return {"ok": True, "evidence": evidence, "isolation": "native-local-skill-overlay",
                    "realExecutionVerified": False, "comparisonIdentity": comparison_identity,
                    "cleanupConfirmed": self._preflight_cleanup,
                    "simulatedTransport": not isinstance(self.transport, NativeTransport)}
        except AdapterError as error:
            return {"ok": False, "reason": str(error), "evidence": evidence,
                    "comparisonIdentity": comparison_identity, "cleanupConfirmed": self._preflight_cleanup}
        except (KeyError, TypeError, ValueError, OSError, AttributeError):
            return {"ok": False, "reason": "native-preflight-incomplete", "evidence": evidence,
                    "comparisonIdentity": comparison_identity, "cleanupConfirmed": self._preflight_cleanup}

    def execute(self, trial, workspace, package, evidence_dir, timeout):
        if isinstance(self.transport, NativeTransport) and os.environ.get(OFFLINE_GUARD):
            return {"started": False, "status": "blocked", "exitCode": None,
                    "cleanupConfirmed": True, "evidence": [], "metrics": {}, "reason": "offline-model-launch-blocked"}
        blocked = {"started": False, "status": "blocked", "exitCode": None,
                   "cleanupConfirmed": True, "evidence": [], "metrics": {}}
        try:
            before = self._user_config_state()
            identity = self._identity(trial, workspace, package)
        except AdapterError as error:
            return {**blocked, "reason": str(error)}
        except (OSError, KeyError, TypeError, ValueError):
            return {**blocked, "reason": "execution-preflight-invalid"}
        if identity in self._ready and self._ready[identity].get("userConfigState") != before:
            self._ready.clear()
            return {**blocked, "reason": "user-config-identity-changed"}
        result = self._execute_impl(trial, workspace, package, evidence_dir, timeout)
        try:
            after = self._user_config_state()
        except AdapterError as error:
            self._ready.clear()
            return {**result, "status": "blocked", "reason": str(error), "userConfigUnchanged": False}
        if before != after:
            self._ready.clear()
            return {**result, "status": "blocked", "reason": "user-config-mutated", "userConfigUnchanged": False}
        result["userConfigUnchanged"] = True if self._guard_user_config else None
        return result

    def _execute_impl(self, trial, workspace, package, evidence_dir, timeout):
        blocked = {"started": False, "status": "blocked", "exitCode": None,
                   "cleanupConfirmed": True, "evidence": [], "metrics": {}}
        if isinstance(self.transport, NativeTransport) and os.environ.get(OFFLINE_GUARD):
            return {**blocked, "reason": "offline-model-launch-blocked"}
        try:
            self._settings(trial, workspace, package)
            identity = self._identity(trial, workspace, package)
            if (identity not in self._ready or type(timeout) not in (int, float)
                    or not math.isfinite(timeout) or timeout <= 0):
                return {**blocked, "reason": "matching-preflight-required"}
            ready = self._ready.pop(identity)
            for path, digest in ready["instructionFiles"].items():
                if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
                    return {**blocked, "reason": "ambient-instruction-identity-changed"}
            expected_executable = ready["executableIdentity"].get("sha256")
            if expected_executable and hashlib.sha256(Path(ready["args"][0]).read_bytes()).hexdigest() != expected_executable:
                return {**blocked, "reason": "executable-identity-changed"}
            response = evidence_dir / "response.txt"
            result = self.transport.capture([*ready["args"], "exec", "--json", "--ephemeral",
                                             "--output-last-message", str(response), "-"], workspace,
                                            evidence_dir / "execution", timeout, stdin=trial["prompt"])
            result.pop("responses", None)
            metrics, complete = parse_events(evidence_dir / "execution.stdout")
            metrics["elapsedSeconds"] = result.pop("elapsedSeconds", None)
            result["metrics"] = metrics
            if response.exists():
                result["evidence"].append(response.name)
            if result["status"] == "completed" and (not complete or not response.is_file()):
                result.update(status="blocked", reason="execution-evidence-incomplete")
            return result
        except AdapterError as error:
            if "result" in locals():
                return {**result, "status": "blocked", "reason": str(error), "metrics": {}}
            return {**blocked, "reason": str(error)}
        except (KeyError, TypeError, ValueError, OSError, AttributeError):
            if "result" in locals():
                return {**result, "status": "blocked", "reason": "execution-evidence-unavailable", "metrics": {}}
            return {**blocked, "reason": "execution-preflight-invalid"}
