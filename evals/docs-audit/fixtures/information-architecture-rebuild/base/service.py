"""Minimal worker entrypoint."""

RETRY_ATTEMPTS = 3


def start() -> str:
    return f"worker started with {RETRY_ATTEMPTS} retry attempts"


if __name__ == "__main__":
    print(start())
