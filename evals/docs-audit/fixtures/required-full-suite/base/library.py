def request_options(url: str, retries: int = 3) -> dict:
    return {"url": url, "retries": retries}
