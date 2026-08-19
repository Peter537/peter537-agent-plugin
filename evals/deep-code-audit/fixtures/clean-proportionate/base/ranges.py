"""Small, direct helpers for inclusive integer ranges."""


def clamp(value: int, lower: int, upper: int) -> int:
    """Return value constrained to the inclusive lower/upper bounds."""
    if lower > upper:
        raise ValueError("lower must not exceed upper")
    return min(max(value, lower), upper)


def contains(value: int, lower: int, upper: int) -> bool:
    """Return whether value is inside the inclusive lower/upper bounds."""
    if lower > upper:
        raise ValueError("lower must not exceed upper")
    return lower <= value <= upper
