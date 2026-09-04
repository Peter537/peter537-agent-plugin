from pathlib import Path


assert Path("package-members.txt").read_text(encoding="utf-8").splitlines() == [
    "bin/review.cmd",
    "lib/review.py",
]

