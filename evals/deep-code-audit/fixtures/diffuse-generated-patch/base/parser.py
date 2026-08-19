"""Parse simple key-value configuration lines."""


def parse_assignment(line: str) -> tuple[str, str]:
    if "=" not in line:
        raise ValueError("assignment must contain =")
    key, value = line.split("=", 1)
    if not key:
        raise ValueError("assignment key is required")
    return key, value
