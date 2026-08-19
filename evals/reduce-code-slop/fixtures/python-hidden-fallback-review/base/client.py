from collections.abc import Callable
from typing import Any


def fetch_identifiers(request: Callable[[], list[dict[str, Any]]]) -> list[str]:
    try:
        records = request()
        return [str(record["id"]) for record in records]
    except Exception:
        return []
