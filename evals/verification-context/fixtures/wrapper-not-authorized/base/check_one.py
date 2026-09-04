from pathlib import Path


assert Path("input.txt").read_text(encoding="utf-8").strip() == "synthetic input"

