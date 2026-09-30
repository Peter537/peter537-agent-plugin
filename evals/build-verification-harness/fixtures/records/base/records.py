def parse_records(text):
    return [line.strip() for line in text.splitlines() if line.strip()]
