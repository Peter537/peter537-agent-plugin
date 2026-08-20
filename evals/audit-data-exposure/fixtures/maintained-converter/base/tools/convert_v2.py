"""Convert supported v1 documents to v2 deterministically."""


def convert(document: dict[str, object]) -> dict[str, object]:
    return {**document, "schema_version": 2}
