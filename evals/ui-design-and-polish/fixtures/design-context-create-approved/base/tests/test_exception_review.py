import unittest

from app.exception_review import can_commit, ordered_evidence


class ExceptionReviewTests(unittest.TestCase):
    def test_orders_evidence_chronologically(self):
        readings = [
            {"recorded_at": "2026-08-25T12:02:00Z"},
            {"recorded_at": "2026-08-25T12:01:00Z"},
        ]
        self.assertEqual(
            "2026-08-25T12:01:00Z", ordered_evidence(readings)[0]["recorded_at"]
        )

    def test_quarantine_requires_confirmation(self):
        self.assertFalse(can_commit("quarantine", False))
        self.assertTrue(can_commit("quarantine", True))


if __name__ == "__main__":
    unittest.main()
