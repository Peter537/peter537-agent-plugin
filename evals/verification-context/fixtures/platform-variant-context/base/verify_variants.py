from pathlib import Path


contract = Path("PLATFORMS.md").read_text(encoding="utf-8")
for required in (
    "py -B tools/windows_check.py",
    "python3 -B posix_check.py",
    "Working directory: repository root",
    "Working directory: `tools/`",
    "discovered-unverified",
):
    assert required in contract
assert Path("tools/windows_check.py").is_file()
assert Path("tools/posix_check.py").is_file()

