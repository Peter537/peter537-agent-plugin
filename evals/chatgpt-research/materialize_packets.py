#!/usr/bin/env python3
"""Materialize offline ChatGPT Research packets with ephemeral privacy canaries."""

from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import shutil
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = SCRIPT_DIR.parents[1].resolve()
MANIFEST_PATH = SCRIPT_DIR / "cases.json"
FIXTURES_ROOT = SCRIPT_DIR / "fixtures"
CASE_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
MAX_FIXTURE_FILE_BYTES = 1024 * 1024


class PacketError(RuntimeError):
    """Raised when packet metadata or materialization is unsafe or invalid."""


def is_link_or_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    except OSError as exc:
        raise PacketError(f"Cannot inspect path: {exc}") from exc
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def validate_fixture_tree(root: Path) -> None:
    if not root.is_dir():
        raise PacketError("Packet fixture directory is missing.")
    if is_link_or_reparse_point(root):
        raise PacketError("Packet fixture root must not be a link or reparse point.")
    pending = [root]
    files = 0
    while pending:
        directory = pending.pop()
        try:
            children = list(directory.iterdir())
        except OSError as exc:
            raise PacketError(f"Cannot inspect packet fixture: {exc}") from exc
        for child in children:
            if is_link_or_reparse_point(child):
                raise PacketError("Packet fixtures must not contain links or reparse points.")
            if child.is_dir():
                pending.append(child)
            else:
                try:
                    metadata = child.stat(follow_symlinks=False)
                except OSError as exc:
                    raise PacketError(f"Cannot inspect packet fixture file: {exc}") from exc
                if not stat.S_ISREG(metadata.st_mode):
                    raise PacketError("Packet fixtures must contain only regular files and directories.")
                if metadata.st_size > MAX_FIXTURE_FILE_BYTES:
                    raise PacketError("Packet fixture file exceeds the 1 MiB safety limit.")
                files += 1
    if files == 0:
        raise PacketError("Packet fixture directory is empty.")


def safe_relative_path(value: Any, context: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise PacketError(f"{context} must be a non-empty relative path.")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise PacketError(f"{context} must be a safe relative path.")
    if path.parts[0].endswith(":") or any("\\" in part for part in path.parts):
        raise PacketError(f"{context} must use a portable relative path.")
    return path


def load_manifest() -> dict[str, Any]:
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PacketError(f"Cannot read packet manifest: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1:
        raise PacketError("Unsupported packet manifest schemaVersion.")
    if manifest.get("suite") != "chatgpt-research":
        raise PacketError("Packet manifest has the wrong suite name.")
    cases = manifest.get("cases")
    if not isinstance(cases, list) or len(cases) < 5:
        raise PacketError("Packet manifest must contain at least five cases.")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise PacketError("Every packet case must be an object.")
        case_id = case.get("id")
        if not isinstance(case_id, str) or CASE_ID_PATTERN.fullmatch(case_id) is None or case_id in seen:
            raise PacketError("Packet manifest contains an unsafe or duplicate case id.")
        seen.add(case_id)
        if case.get("fixture") != case_id:
            raise PacketError(f"Packet case {case_id} must use a matching fixture directory.")
        validate_fixture_tree(FIXTURES_ROOT / case_id)
        canary = case.get("runtimeCanary")
        if canary is not None:
            if not isinstance(canary, dict):
                raise PacketError(f"Packet case {case_id} has invalid runtimeCanary metadata.")
            relative = safe_relative_path(canary.get("path"), f"Packet case {case_id} runtimeCanary.path")
            placeholder = canary.get("placeholder")
            if not isinstance(placeholder, str) or not placeholder:
                raise PacketError(f"Packet case {case_id} runtimeCanary.placeholder must be non-empty.")
            target = FIXTURES_ROOT / case_id / Path(*relative.parts)
            try:
                text = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise PacketError(f"Cannot inspect runtime-canary target for case {case_id}: {exc}") from exc
            if text.count(placeholder) != 1:
                raise PacketError(f"Packet case {case_id} must contain its runtime-canary placeholder exactly once.")
    triggers = manifest.get("triggerCases")
    if not isinstance(triggers, list):
        raise PacketError("Packet manifest must contain triggerCases.")
    activations = sum(trigger.get("expectActivation") is True for trigger in triggers if isinstance(trigger, dict))
    near_misses = sum(trigger.get("expectActivation") is False for trigger in triggers if isinstance(trigger, dict))
    if activations < 6 or near_misses < 4:
        raise PacketError("Trigger coverage requires at least six activations and four near misses.")
    return manifest


def existing_ancestors(path: Path) -> list[Path]:
    ancestors: list[Path] = []
    current = path
    while True:
        if os.path.lexists(current):
            ancestors.append(current)
        if current.parent == current:
            return ancestors
        current = current.parent


def prepare_output(requested: Path) -> Path:
    if ".." in requested.parts:
        raise PacketError("The output path must not contain parent traversal.")
    absolute = Path(os.path.abspath(requested))
    for component in existing_ancestors(absolute):
        if is_link_or_reparse_point(component):
            raise PacketError("The output path must not traverse a link or reparse point.")
    resolved = absolute.resolve()
    try:
        common = Path(os.path.commonpath([str(resolved), str(REPOSITORY_ROOT)]))
    except ValueError:
        common = None
    if common == REPOSITORY_ROOT:
        raise PacketError("The output directory must be outside the source repository.")
    if resolved.exists():
        if not resolved.is_dir():
            raise PacketError("The output path exists and is not a directory.")
        if any(resolved.iterdir()):
            raise PacketError("The output directory must be absent or empty.")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def materialize_case(case: dict[str, Any], output_root: Path) -> None:
    case_id = case["id"]
    destination = output_root / case_id
    if destination.exists():
        raise PacketError("Packet destination already exists.")
    shutil.copytree(FIXTURES_ROOT / case_id, destination)
    canary = case.get("runtimeCanary")
    if canary is None:
        return
    relative = safe_relative_path(canary["path"], f"Packet case {case_id} runtimeCanary.path")
    target = destination / Path(*relative.parts)
    placeholder = canary["placeholder"]
    text = target.read_text(encoding="utf-8")
    target.write_text(text.replace(placeholder, "PRIVATE-" + secrets.token_hex(24), 1), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--list", action="store_true", help="List case ids without writing packets.")
    selection.add_argument("--case", action="append", dest="case_ids", metavar="ID", help="Materialize one case; repeat to select several.")
    selection.add_argument("--all", action="store_true", help="Materialize every packet.")
    parser.add_argument("--output", type=Path, help="Required empty directory outside this repository for materialized packets.")
    return parser.parse_args()


def main() -> int:
    try:
        manifest = load_manifest()
        cases = {case["id"]: case for case in manifest["cases"]}
        args = parse_args()
        if args.list:
            for case_id in sorted(cases):
                print(case_id)
            return 0
        if args.output is None:
            raise PacketError("--output is required when materializing packets.")
        selected = sorted(cases) if args.all else list(dict.fromkeys(args.case_ids or []))
        unknown = [case_id for case_id in selected if case_id not in cases]
        if unknown:
            raise PacketError("Unknown case id(s): " + ", ".join(unknown))
        output_root = prepare_output(args.output)
        for case_id in selected:
            materialize_case(cases[case_id], output_root)
            print(case_id)
        return 0
    except PacketError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
