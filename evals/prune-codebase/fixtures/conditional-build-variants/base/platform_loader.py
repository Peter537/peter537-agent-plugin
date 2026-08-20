import importlib


SUPPORTED_TARGETS = {"linux", "windows"}


def load_separator(target: str) -> str:
    if target not in SUPPORTED_TARGETS:
        raise ValueError(target)
    module = importlib.import_module(f"platforms.{target}")
    return module.separator()
