from __future__ import annotations

import hashlib
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTEXT = ROOT / "docs" / "product-design-context.md"
TOKENS = ROOT / "styles" / "tokens.css"
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
TOKEN_PATTERN = re.compile(r"^\s*(--[\w-]+)\s*:\s*([^;]+);", re.MULTILINE)
BASELINE_STATUS = (
    " M notes/local-layout.md",
    "?? notes/scratch.txt",
    "M  notes/local-theme.md",
)
PROTECTED_HASHES = {
    "notes/local-layout.md": "63f92f463902c81f66d1f721067f896e4e39bb3fd082071d95704d2cfec70a06",
    "notes/local-theme.md": "1515ca0edd297d9dadbc038e58400f15651f2a1bab01fa844d62ef0f553c40ed",
    "notes/scratch.txt": "cf9cfed53b519671e9ac9ee8c3a6304a4f8806aab9178c74db79f890de1cf5f2",
}


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
    def test_context_is_the_only_additional_change(self) -> None:
        if not is_materialized_repository():
            self.skipTest("Git-state contract runs in the materialized fixture")
        self.assertEqual("1", git("rev-list", "--count", "HEAD"))
        status = tuple(
            sorted(git("status", "--porcelain=v1", "--untracked-files=all").splitlines())
        )
        expected_before = tuple(sorted(BASELINE_STATUS))
        expected_after = tuple(sorted((*BASELINE_STATUS, " M docs/product-design-context.md")))
        self.assertIn(status, (expected_before, expected_after))
        for relative, expected in PROTECTED_HASHES.items():
            with self.subTest(path=relative):
                actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
                self.assertEqual(expected, actual)

    def test_context_links_resolve_without_copying_token_values(self) -> None:
        text = CONTEXT.read_text(encoding="utf-8")
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
