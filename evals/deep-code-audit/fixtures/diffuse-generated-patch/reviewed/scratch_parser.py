"""Temporary alternative retained accidentally during the parser change."""


def parse_with_partition(line: str) -> tuple[str, str]:
    key, separator, value = line.partition("=")
    if not separator:
        raise ValueError("assignment must contain =")
    return key.strip(), value.strip()
