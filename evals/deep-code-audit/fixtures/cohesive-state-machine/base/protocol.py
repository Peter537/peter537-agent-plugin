"""Explicit state machine for the documented transfer protocol."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class State(Enum):
    NEW = auto()
    NEGOTIATING = auto()
    READY = auto()
    TRANSFERRING = auto()
    RECOVERING = auto()
    COMPLETE = auto()
    FAILED = auto()


class ProtocolError(RuntimeError):
    """Raised when a caller requests an invalid transition."""


@dataclass
class TransferSession:
    state: State = State.NEW
    acknowledged_chunks: int = 0

    def begin_negotiation(self) -> None:
        self._require(State.NEW)
        self.state = State.NEGOTIATING

    def accept_peer(self) -> None:
        self._require(State.NEGOTIATING)
        self.state = State.READY

    def begin_transfer(self) -> None:
        self._require(State.READY)
        self.state = State.TRANSFERRING

    def recover(self) -> None:
        self._require(State.RECOVERING)
        self.state = State.READY

    def acknowledge_chunk(self) -> None:
        self._require(State.TRANSFERRING)
        self.acknowledged_chunks += 1

    def lose_connection(self) -> None:
        self._require(State.TRANSFERRING)
        self.state = State.RECOVERING

    def complete(self) -> None:
        self._require(State.TRANSFERRING)
        if self.acknowledged_chunks == 0:
            raise ProtocolError("At least one chunk must be acknowledged.")
        self.state = State.COMPLETE

    def fail(self) -> None:
        if self.state in {State.COMPLETE, State.FAILED}:
            raise ProtocolError("A terminal session cannot fail again.")
        self.state = State.FAILED

    def _require(self, *allowed: State) -> None:
        if self.state not in allowed:
            expected = ", ".join(state.name for state in allowed)
            raise ProtocolError(f"Expected {expected}; found {self.state.name}.")
