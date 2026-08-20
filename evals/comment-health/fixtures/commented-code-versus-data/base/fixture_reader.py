from pathlib import Path


def fixture_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()
