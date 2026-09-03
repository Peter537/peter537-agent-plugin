def parse_rows(text: str) -> list[str]:
    return [line for line in text.splitlines() if line]
