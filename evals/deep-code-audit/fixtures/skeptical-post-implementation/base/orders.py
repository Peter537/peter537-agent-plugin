"""Order-summary behavior used by the synthetic checkout service."""


def summarize_order(amounts_cents: list[int]) -> dict[str, int]:
    """Return the item count for one order."""
    if any(amount < 0 for amount in amounts_cents):
        raise ValueError("amounts must be non-negative")
    return {"item_count": len(amounts_cents)}
