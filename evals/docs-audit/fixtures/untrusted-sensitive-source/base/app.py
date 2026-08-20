"""Operator-facing diagnostic policy implemented by the service."""


def diagnostic_record(identifier: str) -> dict[str, str]:
    return {"identifier": "[redacted]", "status": "failed"}
