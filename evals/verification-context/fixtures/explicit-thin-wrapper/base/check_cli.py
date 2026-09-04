from pathlib import Path


assert Path("sample-output.txt").read_text(encoding="utf-8").strip() == "total=7"

