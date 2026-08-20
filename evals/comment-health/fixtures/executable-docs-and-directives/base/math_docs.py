def clamp(value: int, minimum: int, maximum: int) -> int:
    """Clamp a value to an inclusive interval.

    >>> clamp(12, 0, 10)
    10
    >>> clamp(-1, 0, 10)
    0
    """
    return min(maximum, max(minimum, value))
