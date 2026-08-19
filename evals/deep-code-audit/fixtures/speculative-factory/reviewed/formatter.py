"""Formatting used by the synthetic status page."""

from typing import Protocol


class Formatter(Protocol):
    def format(self, title: str, body: str) -> str: ...


class PlainFormatter:
    def format(self, title: str, body: str) -> str:
        clean_title = title.strip()
        clean_body = body.strip()
        if not clean_title or not clean_body:
            raise ValueError("title and body are required")
        return f"{clean_title}: {clean_body}"


class FormatterRegistry:
    def __init__(self) -> None:
        self._formatters: dict[str, Formatter] = {"plain": PlainFormatter()}

    def resolve(self, mode: str) -> Formatter:
        try:
            return self._formatters[mode]
        except KeyError as exc:
            raise ValueError(f"unsupported format: {mode}") from exc


class FormatterFactory:
    @staticmethod
    def create(mode: str) -> Formatter:
        return FormatterRegistry().resolve(mode)


def format_message(title: str, body: str) -> str:
    """Render the only supported status-message format."""
    formatter = FormatterFactory.create("plain")
    return formatter.format(title, body)
