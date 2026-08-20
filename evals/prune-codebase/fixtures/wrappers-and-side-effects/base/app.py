import plugins  # noqa: F401 -- import registers built-in handlers
from registry import HANDLERS


def available_handlers() -> list[str]:
    return list(HANDLERS)
