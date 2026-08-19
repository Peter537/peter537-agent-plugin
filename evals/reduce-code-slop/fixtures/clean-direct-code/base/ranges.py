def clamp(value: int, minimum: int, maximum: int) -> int:
    if minimum > maximum:
        raise ValueError("minimum must not exceed maximum")
    return min(maximum, max(minimum, value))
