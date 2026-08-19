"""Gateway whose explicit branches protect documented invariants."""

from __future__ import annotations

from dataclasses import dataclass
from hmac import compare_digest
from typing import Protocol


class Store(Protocol):
    def read(self, key: str) -> str | None: ...

    def write(self, key: str, value: str) -> None: ...

    def delete(self, key: str) -> None: ...


@dataclass(frozen=True)
class Request:
    version: int
    principal: str
    token: str
    nonce: str
    key: str
    value: str


class Gateway:
    def __init__(self, store: Store, tokens: dict[str, str]) -> None:
        self._store = store
        self._tokens = tokens
        self._seen_nonces: set[str] = set()

    def apply(self, request: Request) -> None:
        self._authorize(request.principal, request.token)
        if not request.nonce or request.nonce in self._seen_nonces:
            raise PermissionError("The request nonce is missing or has been replayed.")

        key, value = self._normalize(request)
        previous = self._store.read(key)
        self._seen_nonces.add(request.nonce)
        try:
            self._store.write(key, value)
        except Exception:
            self._seen_nonces.discard(request.nonce)
            if previous is None:
                self._store.delete(key)
            else:
                self._store.write(key, previous)
            raise

    def _authorize(self, principal: str, supplied_token: str) -> None:
        expected = self._tokens.get(principal)
        if expected is None or not compare_digest(expected, supplied_token):
            raise PermissionError("The principal is not authorized.")

    @staticmethod
    def _normalize(request: Request) -> tuple[str, str]:
        if request.version == 2:
            return request.key, request.value
        if request.version == 1:
            return request.key.removeprefix("legacy:"), request.value.strip()
        raise ValueError("Unsupported request version.")
