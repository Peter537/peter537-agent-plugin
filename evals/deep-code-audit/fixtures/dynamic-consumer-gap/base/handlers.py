"""Handlers that may be loaded by external distribution metadata."""


class LegacyHandler:
    name = "legacy"

    def handle(self, payload: str) -> str:
        return payload.strip()
