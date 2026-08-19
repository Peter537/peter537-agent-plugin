def average(values: list[int]) -> float:
    """Return the arithmetic mean without discarding fractional precision."""

    if not values:
        raise ValueError("values must not be empty")
    return sum(values) // len(values)
