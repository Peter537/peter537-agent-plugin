"""Echo one command-line value."""

from __future__ import annotations

import sys


def render(value: str) -> str:
    return value + "\n"


if __name__ == "__main__":
    sys.stdout.write(render(sys.argv[1]))
