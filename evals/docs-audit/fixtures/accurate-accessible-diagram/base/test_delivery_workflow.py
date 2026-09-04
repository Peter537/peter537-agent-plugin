import unittest
from pathlib import Path

from delivery_workflow import DeliveryWorkflow


class DeliveryWorkflowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.database_path = Path.cwd() / f".fixture-{self._testMethodName}.sqlite3"
        self.assertFalse(self.database_path.exists())
        self.addCleanup(self._remove_database)
        self.workflow = DeliveryWorkflow(self.database_path)

    def _remove_database(self) -> None:
        for suffix in ("", "-shm", "-wal"):
            Path(f"{self.database_path}{suffix}").unlink(missing_ok=True)

    def test_acceptance_validates_before_durable_enqueue(self) -> None:
        with self.assertRaises(ValueError):
            self.workflow.accept("", "payload")
        self.assertEqual(self.workflow.count("queue"), 0)

        self.workflow.accept("record-1", "payload")

        self.assertEqual(self.workflow.events[:2], ["validated", "queued"])
        self.assertEqual(self.workflow.count("queue"), 1)

    def test_processing_persists_before_creating_outbox_entry(self) -> None:
        self.workflow.accept("record-2", "payload")

        self.assertTrue(self.workflow.process_next())

        self.assertLess(
            self.workflow.events.index("persisted"),
            self.workflow.events.index("outbox-appended"),
        )
        self.assertEqual(self.workflow.count("records"), 1)
        self.assertEqual(self.workflow.count("outbox"), 1)
        self.assertEqual(self.workflow.count("queue"), 0)

    async def test_notification_failure_preserves_record_and_outbox(self) -> None:
        self.workflow.accept("record-3", "payload")
        self.workflow.process_next()

        async def fail_delivery(_record_id: str, _payload: str) -> None:
            raise RuntimeError("notification delivery failed")

        with self.assertRaises(RuntimeError):
            await self.workflow.dispatch_next(fail_delivery)

        self.assertEqual(self.workflow.count("records"), 1)
        self.assertEqual(self.workflow.count("outbox"), 1)
        self.assertNotIn("notification-sent", self.workflow.events)


if __name__ == "__main__":
    unittest.main()
