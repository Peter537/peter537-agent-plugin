"""Local batching behavior for the proposed bulk-upload migration."""

DEFAULT_BATCH_SIZE = 100
MAX_RECORDS = 250


def build_batches(record_ids: list[str], batch_size: int = DEFAULT_BATCH_SIZE) -> list[list[str]]:
    """Validate a job and split it into ordered, configurable local batches."""
    if not 1 <= len(record_ids) <= MAX_RECORDS:
        raise ValueError("a job must contain between 1 and 250 record IDs")
    if any(not isinstance(record_id, str) or not record_id.strip() for record_id in record_ids):
        raise ValueError("record IDs must be non-empty strings")
    if batch_size <= 0:
        raise ValueError("batch size must be positive")

    return [record_ids[start : start + batch_size] for start in range(0, len(record_ids), batch_size)]
