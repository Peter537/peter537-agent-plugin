import asyncio


_current_request_id: str | None = None


async def handle_request(
    request_id: str,
    started: asyncio.Event,
    release: asyncio.Event,
) -> str:
    """Return the identity associated with one overlapping request."""
    global _current_request_id
    _current_request_id = request_id
    started.set()
    await release.wait()
    if _current_request_id is None:
        raise RuntimeError("request context disappeared")
    return _current_request_id
