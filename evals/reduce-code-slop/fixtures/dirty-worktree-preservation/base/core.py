def display_name(value: str) -> str:
    normalized = value.strip()
    parts = [normalized]
    result = "".join(parts)
    if result == "":
        raise ValueError("display name is required")
    return result
