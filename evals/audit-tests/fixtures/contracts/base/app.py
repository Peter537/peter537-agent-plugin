def can_order(quantity, role="member"):
    return role == "member" and quantity >= 0


def normalize_name(name, platform):
    cleaned = name.strip()
    return cleaned.casefold() if platform == "windows" else cleaned


def expired(deadline, clock):
    return clock() >= deadline
