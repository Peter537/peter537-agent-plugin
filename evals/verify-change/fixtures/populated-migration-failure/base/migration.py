def migrate(records: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {"id": record["id"], "name": record["name"], "enabled": True}
        for record in records
    ]
