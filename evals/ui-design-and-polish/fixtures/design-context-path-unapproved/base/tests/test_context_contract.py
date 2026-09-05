from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UNAPPROVED_PATHS = (
    ROOT / "docs" / "product-design-context.md",
    ROOT / "PRODUCT.md",
    ROOT / "DESIGN.md",
)


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *arguments],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.rstrip("\r\n")


def is_materialized_repository() -> bool:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--show-toplevel"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
    )
    return result.returncode == 0 and Path(result.stdout.strip()).resolve() == ROOT


class ContextContractTests(unittest.TestCase):
    def test_no_unapproved_context_path_is_created(self) -> None:
        for path in UNAPPROVED_PATHS:
            self.assertFalse(path.exists(), path.relative_to(ROOT))

    def test_repository_remains_unchanged(self) -> None:
        if not is_materialized_repository():
            self.skipTest("Git-state contract runs in the materialized fixture")
        self.assertEqual("1", git("rev-list", "--count", "HEAD"))
        self.assertEqual("", git("status", "--porcelain=v1", "--untracked-files=all"))


if __name__ == "__main__":
    unittest.main()
