from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "docs" / "product-design-context.md"
TOKENS = ROOT / "styles" / "tokens.css"
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
TOKEN_PATTERN = re.compile(r"^\s*(--[\w-]+)\s*:\s*([^;]+);", re.MULTILINE)


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
    def test_only_the_approved_context_path_can_change(self) -> None:
        if not is_materialized_repository():
            self.skipTest("Git-state contract runs in the materialized fixture")
        self.assertEqual("1", git("rev-list", "--count", "HEAD"))
        status = tuple(
            sorted(git("status", "--porcelain=v1", "--untracked-files=all").splitlines())
        )
        self.assertIn(status, ((), ("?? docs/product-design-context.md",)))

    def test_context_links_and_token_values_when_created(self) -> None:
        if not CONTEXT.exists():
            return
        text = CONTEXT.read_text(encoding="utf-8")
        self.assertTrue(text.strip())
        for raw_target in LINK_PATTERN.findall(text):
            target = raw_target.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (CONTEXT.parent / target).resolve()
            self.assertTrue(resolved.is_relative_to(ROOT), target)
            self.assertTrue(resolved.is_file(), target)
        for name, value in TOKEN_PATTERN.findall(TOKENS.read_text(encoding="utf-8")):
            with self.subTest(token=name):
                self.assertNotIn(value.strip().casefold(), text.casefold())


if __name__ == "__main__":
    unittest.main()
