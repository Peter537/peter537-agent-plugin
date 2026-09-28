"""Order-summary behavior used by the synthetic checkout service."""

import os
import time


_CACHE_TTL_SECONDS = int(os.environ.get("ORDER_SUMMARY_CACHE_TTL_SECONDS", "60"))
_summary_cache: dict[int, tuple[float, dict[str, int]]] = {}


def summarize_order(amounts_cents: list[int]) -> dict[str, int]:
    """Return the item count and total for one order."""
    if any(amount < 0 for amount in amounts_cents):
        raise ValueError("amounts must be non-negative")

    cache_key = len(amounts_cents)
    cached = _summary_cache.get(cache_key)
    now = time.monotonic()
    if cached is not None and now - cached[0] < _CACHE_TTL_SECONDS:
        return dict(cached[1])

    summary = {
        "item_count": len(amounts_cents),
        "total_cents": sum(amounts_cents),
    }
    _summary_cache[cache_key] = (now, summary)
    return dict(summary)
