import unittest

from app.dispatch import can_assign, ordered_routes


class DispatchTests(unittest.TestCase):
    def test_queue_order_is_preserved(self):
        routes = [{"queue_position": 2}, {"queue_position": 1}]
        self.assertEqual(1, ordered_routes(routes)[0]["queue_position"])

    def test_assignment_requires_permission_and_confirmation(self):
        self.assertFalse(can_assign("view", True))
        self.assertFalse(can_assign("assign", False))
        self.assertTrue(can_assign("assign", True))


if __name__ == "__main__":
    unittest.main()
