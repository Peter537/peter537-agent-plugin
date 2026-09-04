"""Exercise the populated migration in an isolated copy and clean it up."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from migrate import migrate


ROOT = Path(__file__).resolve().parent


def repository_path(value: str, *, must_exist: bool) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError("paths must be repository-relative")
    resolved = (ROOT / candidate).resolve(strict=False)
    resolved.relative_to(ROOT)
    if must_exist and not resolved.is_file():
        raise ValueError("the dataset is unavailable")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--workdir", required=True)
    args = parser.parse_args()

    try:
        dataset = repository_path(args.dataset, must_exist=True)
        workdir = repository_path(args.workdir, must_exist=False)
    except (OSError, ValueError):
        return 2
    runtime_root = ROOT / ".runtime"
    if workdir.parent != runtime_root or runtime_root.exists() or workdir.exists():
        return 2

    original = dataset.read_bytes()
    created_runtime = False
    try:
        workdir.mkdir(parents=True)
        created_runtime = True
        copied = workdir / "source.json"
        output = workdir / "migrated.json"
        shutil.copyfile(dataset, copied)
        migrate(copied, output)
        result = json.loads(output.read_text(encoding="utf-8"))
        if result != {
            "format": 2,
            "records": [
                {"record_id": "synthetic-a", "state": "active"},
                {"record_id": "synthetic-b", "state": "paused"},
                {"record_id": "synthetic-c", "state": "active"},
            ],
        }:
            return 1
        if dataset.read_bytes() != original or copied.read_bytes() != original:
            return 1
        return 0
    finally:
        if created_runtime and workdir.exists():
            shutil.rmtree(workdir)
        if created_runtime and runtime_root.exists() and not any(runtime_root.iterdir()):
            runtime_root.rmdir()


if __name__ == "__main__":
    raise SystemExit(main())
