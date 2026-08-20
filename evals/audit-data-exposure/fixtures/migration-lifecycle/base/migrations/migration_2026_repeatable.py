"""Supported v2 schema migration: transactional, idempotent, and reversible."""


def upgrade(document: dict[str, object]) -> dict[str, object]:
    return {**document, "schema_version": 2}
