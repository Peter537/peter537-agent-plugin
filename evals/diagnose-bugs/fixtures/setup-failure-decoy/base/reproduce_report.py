from pathlib import Path


fixture = Path("optional/customer-export.json")
if not fixture.exists():
    print("SETUP-12: optional customer export fixture is unavailable")
    raise SystemExit(2)
print("REPORT-77: expected total 42 but received 41")
raise SystemExit(1)
