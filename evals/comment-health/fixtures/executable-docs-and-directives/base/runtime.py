from typing import Any


def legacy_name(value: Any) -> str:
    # type: ignore[no-any-return] -- legacy SDK has no type declarations
    return value.name


def platform_only() -> None:  # pragma: no cover -- exercised by the platform harness
    raise RuntimeError("platform harness only")
