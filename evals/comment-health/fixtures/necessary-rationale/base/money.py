def cents_to_display_units(cents: int) -> str:
    # Storage and API boundaries use integer cents; formatting is the only decimal boundary.
    return f"{cents / 100:.2f}"
