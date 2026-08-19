import json
from typing import Any, NamedTuple, cast


class Settings(NamedTuple):
    region: str
    retries: int


def decode_settings(raw: str) -> Settings:
    decoded: Any = json.loads(raw)
    payload = cast(dict[str, Any], decoded)
    try:
        region = cast(str, payload["region"])
        retries = cast(int, payload["retries"])
        return Settings(region=region.strip(), retries=retries)
    except (AttributeError, KeyError, TypeError) as exc:
        raise ValueError("Unsupported settings payload") from exc
