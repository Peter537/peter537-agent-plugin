import unittest

from reconcile import reconcile


class ReconcileTests(unittest.TestCase):
    def test_reports_missing_in_expected_order(self) -> None:
        missing, _ = reconcile(["a", "b", "c"], ["a"])
        self.assertEqual(missing, ["b", "c"])


if __name__ == "__main__":
    unittest.main()
