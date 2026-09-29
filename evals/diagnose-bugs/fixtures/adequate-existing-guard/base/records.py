def parse_records(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[:-1]
