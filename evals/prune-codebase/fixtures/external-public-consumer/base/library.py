def calculate_export_checksum(payload: bytes) -> int:
    """Return the checksum used by supported external export clients."""
    return sum(payload) % 256


def internal_summary(values: list[int]) -> int:
    return sum(values)
