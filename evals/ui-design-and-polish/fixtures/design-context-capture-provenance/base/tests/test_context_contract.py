from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "docs" / "product-design-context.md"
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


class ContextContractTests(unittest.TestCase):
    def test_only_context_may_change_and_index_is_preserved(self) -> None:
        if Path(git("rev-parse", "--show-toplevel")).resolve() != ROOT:
            self.skipTest("Git-state contract runs in the materialized fixture")
        self.assertEqual("1", git("rev-list", "--count", "HEAD"))
        self.assertEqual("", git("diff", "--cached", "--name-only"))
        status = tuple(git("status", "--porcelain=v1", "--untracked-files=all").splitlines())
        self.assertIn(status, ((), (" M docs/product-design-context.md",)))

    def test_context_links_resolve_without_copying_token_values(self) -> None:
        text = CONTEXT.read_text(encoding="utf-8")
        self.assertTrue(text.strip())
        for raw_target in LINK_PATTERN.findall(text):
            target = raw_target.split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (CONTEXT.parent / target).resolve()
            self.assertTrue(resolved.is_relative_to(ROOT), target)
            self.assertTrue(resolved.is_file(), target)
        tokens = (ROOT / "styles" / "tokens.css").read_text(encoding="utf-8")
        for name, value in TOKEN_PATTERN.findall(tokens):
            with self.subTest(token=name):
                self.assertNotIn(value.strip().casefold(), text.casefold())


if __name__ == "__main__":
    unittest.main()
