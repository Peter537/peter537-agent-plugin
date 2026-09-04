from __future__ import annotations


def reject_record(record_id: str) -> dict[str, str]:
    if not record_id.strip():
        raise ValueError("record_id is required")
    return {"id": record_id, "state": "rejected"}

