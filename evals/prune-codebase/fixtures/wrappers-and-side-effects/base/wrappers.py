from collections.abc import Callable
from datetime import datetime, timezone


def current_timestamp(clock: Callable[[], datetime] | None = None) -> str:
    selected_clock = clock or (lambda: datetime.now(timezone.utc))
    return selected_clock().isoformat()
