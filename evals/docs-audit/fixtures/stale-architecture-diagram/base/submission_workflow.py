"""Small durable submission workflow used by the documentation fixture."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class Submission:
    record_id: str
    payload: str


@dataclass(frozen=True)
class Notification:
    record_id: str
    payload: str


class NotificationDeliveryError(RuntimeError):
    """Raised when the configured notifier cannot deliver a message."""


class EventLog:
    """Record observable component ordering for the fixture tests."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def record(self, event: str) -> None:
        self.events.append(event)


class WorkflowDatabase:
    """Own the SQLite schema shared by the durable workflow components."""

    def __init__(self, path: Path) -> None:
        self.path = path
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS submission_queue (
                    position INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL UNIQUE,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS submissions (
                    record_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS notification_outbox (
                    position INTEGER PRIMARY KEY AUTOINCREMENT,
                    record_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                """
            )

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()


class DurableQueue:
    def __init__(self, database: WorkflowDatabase, events: EventLog) -> None:
        self.database = database
        self.events = events

    def enqueue(self, submission: Submission) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO submission_queue(record_id, payload) VALUES (?, ?)",
                (submission.record_id, submission.payload),
            )
        self.events.record("queue.enqueued")

    def peek(self) -> Submission | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT record_id, payload FROM submission_queue ORDER BY position LIMIT 1"
            ).fetchone()
        return None if row is None else Submission(record_id=row[0], payload=row[1])

    def complete(self, record_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "DELETE FROM submission_queue WHERE record_id = ?", (record_id,)
            )
        self.events.record("queue.completed")

    def count(self) -> int:
        with self.database.connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM submission_queue").fetchone()
        assert row is not None
        return int(row[0])


class DurableStore:
    def __init__(self, database: WorkflowDatabase, events: EventLog) -> None:
        self.database = database
        self.events = events

    def persist(self, submission: Submission) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO submissions(record_id, payload) VALUES (?, ?)",
                (submission.record_id, submission.payload),
            )
        self.events.record("store.persisted")

    def get(self, record_id: str) -> Submission | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT record_id, payload FROM submissions WHERE record_id = ?",
                (record_id,),
            ).fetchone()
        return None if row is None else Submission(record_id=row[0], payload=row[1])


class Outbox:
    def __init__(self, database: WorkflowDatabase, events: EventLog) -> None:
        self.database = database
        self.events = events

    def append(self, notification: Notification) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO notification_outbox(record_id, payload) VALUES (?, ?)",
                (notification.record_id, notification.payload),
            )
        self.events.record("outbox.appended")

    def peek(self) -> Notification | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT record_id, payload FROM notification_outbox "
                "ORDER BY position LIMIT 1"
            ).fetchone()
        return None if row is None else Notification(record_id=row[0], payload=row[1])

    def mark_sent(self, record_id: str) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "DELETE FROM notification_outbox WHERE position = ("
                "SELECT position FROM notification_outbox "
                "WHERE record_id = ? ORDER BY position LIMIT 1)",
                (record_id,),
            )
        self.events.record("outbox.sent")

    def count(self) -> int:
        with self.database.connect() as connection:
            row = connection.execute("SELECT COUNT(*) FROM notification_outbox").fetchone()
        assert row is not None
        return int(row[0])


class SubmissionAPI:
    def __init__(self, queue: DurableQueue, events: EventLog) -> None:
        self.queue = queue
        self.events = events

    def accept(self, record_id: str, payload: str) -> None:
        if not record_id.strip() or not payload.strip():
            raise ValueError("record_id and payload must be non-empty")
        self.events.record("api.validated")
        self.queue.enqueue(Submission(record_id=record_id, payload=payload))


class SubmissionWorker:
    def __init__(
        self,
        queue: DurableQueue,
        store: DurableStore,
        outbox: Outbox,
    ) -> None:
        self.queue = queue
        self.store = store
        self.outbox = outbox

    def process_next(self) -> bool:
        submission = self.queue.peek()
        if submission is None:
            return False
        self.store.persist(submission)
        self.outbox.append(
            Notification(record_id=submission.record_id, payload=submission.payload)
        )
        self.queue.complete(submission.record_id)
        return True


class Notifier(Protocol):
    async def send(self, notification: Notification) -> None: ...


class NotificationDispatcher:
    def __init__(self, outbox: Outbox, notifier: Notifier, events: EventLog) -> None:
        self.outbox = outbox
        self.notifier = notifier
        self.events = events

    async def dispatch_next(self) -> bool:
        notification = self.outbox.peek()
        if notification is None:
            return False
        self.events.record("notification.attempted")
        await self.notifier.send(notification)
        self.outbox.mark_sent(notification.record_id)
        return True
