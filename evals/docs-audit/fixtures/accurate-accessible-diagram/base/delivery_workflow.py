"""Durable event delivery used by the documentation evaluation fixture."""

from __future__ import annotations

import sqlite3
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from pathlib import Path


class DeliveryWorkflow:
    """Keep submission durability separate from notification delivery."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.events: list[str] = []
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE queue (record_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE records (record_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE outbox (record_id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                """
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def accept(self, record_id: str, payload: str) -> None:
        if not record_id.strip() or not payload.strip():
            raise ValueError("record_id and payload must be non-empty")
        self.events.append("validated")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO queue(record_id, payload) VALUES (?, ?)",
                (record_id, payload),
            )
        self.events.append("queued")

    def process_next(self) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_id, payload FROM queue ORDER BY rowid LIMIT 1"
            ).fetchone()
        if row is None:
            return False
        with self._connect() as connection:
            connection.execute("INSERT INTO records VALUES (?, ?)", row)
        self.events.append("persisted")
        with self._connect() as connection:
            connection.execute("INSERT INTO outbox VALUES (?, ?)", row)
        self.events.append("outbox-appended")
        with self._connect() as connection:
            connection.execute("DELETE FROM queue WHERE record_id = ?", (row[0],))
        self.events.append("queue-completed")
        return True

    async def dispatch_next(
        self, sender: Callable[[str, str], Awaitable[None]]
    ) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_id, payload FROM outbox ORDER BY rowid LIMIT 1"
            ).fetchone()
        if row is None:
            return False
        self.events.append("notification-attempted")
        await sender(str(row[0]), str(row[1]))
        with self._connect() as connection:
            connection.execute("DELETE FROM outbox WHERE record_id = ?", (row[0],))
        self.events.append("notification-sent")
        return True

    def count(self, table: str) -> int:
        if table not in {"queue", "records", "outbox"}:
            raise ValueError("unsupported table")
        with self._connect() as connection:
            row = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        assert row is not None
        return int(row[0])
