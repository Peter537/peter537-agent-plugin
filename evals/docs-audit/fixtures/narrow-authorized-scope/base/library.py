"""Public retry client."""


def request(url: str, retries: int = 3) -> tuple[str, int]:
    return url, retries
