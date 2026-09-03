import json
from pathlib import Path


def normalize_title(value: str) -> str:
    return " ".join(value.split()).strip()


def publish(path: Path, title: str) -> None:
    record = {"title": normalize_title(title), "status": "draft"}
    path.write_text(json.dumps(record), encoding="utf-8")


def reload(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))
