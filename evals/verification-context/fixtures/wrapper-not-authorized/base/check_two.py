from pathlib import Path


assert Path("output.txt").read_text(encoding="utf-8").strip() == "accepted"

