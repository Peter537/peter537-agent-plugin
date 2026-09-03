"""Current local request planning for the Provider v2 uploader."""

MAX_REQUEST_SIZE = 80


def plan_requests(record_ids: list[str]) -> list[list[str]]:
    """Validate all IDs and construct ordered provider requests."""
    if not record_ids or any(not isinstance(record_id, str) or not record_id.strip() for record_id in record_ids):
        raise ValueError("record IDs must be non-empty strings")
    return [
        record_ids[start : start + MAX_REQUEST_SIZE]
        for start in range(0, len(record_ids), MAX_REQUEST_SIZE)
    ]
