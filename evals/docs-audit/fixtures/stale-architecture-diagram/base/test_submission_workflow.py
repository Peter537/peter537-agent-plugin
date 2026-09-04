import unittest
from pathlib import Path

from submission_workflow import (
    DurableQueue,
    DurableStore,
    EventLog,
    Notification,
    NotificationDeliveryError,
    NotificationDispatcher,
    Outbox,
    Submission,
    SubmissionAPI,
    SubmissionWorker,
    WorkflowDatabase,
)


class RecordingNotifier:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[Notification] = []

    async def send(self, notification: Notification) -> None:
        if self.fail:
            raise NotificationDeliveryError("notification delivery failed")
        self.sent.append(notification)


class SubmissionWorkflowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.database_path = Path.cwd() / f".fixture-{self._testMethodName}.sqlite3"
        self.assertFalse(self.database_path.exists())
        self.addCleanup(self._remove_database)
        database = WorkflowDatabase(self.database_path)
        self.events = EventLog()
        self.queue = DurableQueue(database, self.events)
        self.store = DurableStore(database, self.events)
        self.outbox = Outbox(database, self.events)
        self.api = SubmissionAPI(self.queue, self.events)
        self.worker = SubmissionWorker(self.queue, self.store, self.outbox)

    def _remove_database(self) -> None:
        for suffix in ("", "-shm", "-wal"):
            Path(f"{self.database_path}{suffix}").unlink(missing_ok=True)

    def test_validation_precedes_durable_enqueue(self) -> None:
        with self.assertRaises(ValueError):
            self.api.accept("", "payload")
        self.assertEqual(self.queue.count(), 0)

        self.api.accept("record-1", "payload")

        self.assertEqual(self.events.events[:2], ["api.validated", "queue.enqueued"])
        self.assertEqual(self.queue.count(), 1)

    def test_worker_persists_before_creating_outbox_entry(self) -> None:
        self.api.accept("record-2", "payload")

        self.assertTrue(self.worker.process_next())

        self.assertEqual(
            self.store.get("record-2"), Submission(record_id="record-2", payload="payload")
        )
        self.assertLess(
            self.events.events.index("store.persisted"),
            self.events.events.index("outbox.appended"),
        )
        self.assertEqual(self.queue.count(), 0)
        self.assertEqual(self.outbox.count(), 1)

    async def test_notification_failure_preserves_durable_state(self) -> None:
        self.api.accept("record-3", "payload")
        self.worker.process_next()
        dispatcher = NotificationDispatcher(
            self.outbox, RecordingNotifier(fail=True), self.events
        )

        with self.assertRaises(NotificationDeliveryError):
            await dispatcher.dispatch_next()

        self.assertIsNotNone(self.store.get("record-3"))
        self.assertEqual(self.outbox.count(), 1)
        self.assertNotIn("outbox.sent", self.events.events)

    async def test_successful_notification_clears_outbox_entry(self) -> None:
        self.api.accept("record-4", "payload")
        self.worker.process_next()
        notifier = RecordingNotifier()
        dispatcher = NotificationDispatcher(self.outbox, notifier, self.events)

        self.assertTrue(await dispatcher.dispatch_next())

        self.assertEqual(len(notifier.sent), 1)
        self.assertIsNotNone(self.store.get("record-4"))
        self.assertEqual(self.outbox.count(), 0)


if __name__ == "__main__":
    unittest.main()
