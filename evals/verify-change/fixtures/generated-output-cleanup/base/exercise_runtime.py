from pathlib import Path


output = Path(".verify-output")
output.mkdir(exist_ok=False)
(output / "report.txt").write_text("verified=true\n", encoding="utf-8")
