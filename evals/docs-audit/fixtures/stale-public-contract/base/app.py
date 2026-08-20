"""Public contract used by the fixture tests."""

ROUTE = "/v2/items"


def response() -> dict[str, list[dict[str, str]]]:
    return {"items": [{"title": "Example"}]}
