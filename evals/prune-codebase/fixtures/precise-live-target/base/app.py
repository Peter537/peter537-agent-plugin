def health_status() -> dict[str, str]:
    return {"status": "ok"}


def main() -> dict[str, str]:
    return health_status()
