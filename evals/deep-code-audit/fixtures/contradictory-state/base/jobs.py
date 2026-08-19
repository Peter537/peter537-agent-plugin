"""Intentionally flawed lifecycle state for audit evaluation."""

from dataclasses import dataclass


@dataclass
class Job:
    is_running: bool = False
    is_complete: bool = False
    has_failed: bool = False

    def start(self) -> None:
        self.is_running = True

    def complete(self) -> None:
        self.is_running = False
        self.is_complete = True

    def fail(self) -> None:
        self.is_running = False
        self.has_failed = True
