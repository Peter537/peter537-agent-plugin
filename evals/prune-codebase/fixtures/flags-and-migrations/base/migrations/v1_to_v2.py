def migrate(record: dict[str, object]) -> dict[str, object]:
    result = dict(record)
    result["schema_version"] = 2
    return result
