from importlib import import_module
from typing import Protocol, cast


class Factory(Protocol):
    def create(self) -> str: ...


def load_factory(coordinate: str) -> Factory:
    module_name, separator, member_name = coordinate.partition(":")
    if not separator or not module_name or not member_name:
        raise ValueError("Expected module:factory")
    module = import_module(module_name)
    factory = getattr(module, member_name)
    if not callable(getattr(factory, "create", None)):
        raise TypeError("Plugin factory must expose create()")
    return cast(Factory, factory)
