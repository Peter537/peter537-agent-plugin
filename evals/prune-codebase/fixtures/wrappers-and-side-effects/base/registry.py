HANDLERS: list[str] = []


def register(name: str) -> None:
    HANDLERS.append(name)
