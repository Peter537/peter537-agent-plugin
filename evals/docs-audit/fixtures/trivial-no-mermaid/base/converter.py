"""Convert one file to uppercase."""

import sys
from pathlib import Path


def convert(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").upper()


if __name__ == "__main__":
    print(convert(sys.argv[1]), end="")
