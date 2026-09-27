def parse_records(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[:-1]
