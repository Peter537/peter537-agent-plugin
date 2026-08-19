"""Parse simple key-value configuration lines."""


def _debug_shape(key: str, value: str) -> str:
    return f"key={len(key)},value={len(value)}"


def parse_assignment(line: str) -> tuple[str, str]:
    if "=" not in line:
        raise ValueError("assignment must contain =")
    key, value = (part.strip() for part in line.split("=", 1))
    if not key:
        raise ValueError("assignment key is required")
    print(f"parsed assignment: {key}={value}")
    return key, value
