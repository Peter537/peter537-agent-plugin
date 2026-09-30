"""Characterize local operations; green probes are not a security verdict."""
import unittest

from roles import approve_order, cancel_order, can_show_approval


class RoleBoundaryTests(unittest.TestCase):
    def test_current_manager_and_wrong_tenant(self):
        session = {"subject": "alice", "tenant": "north", "role": "manager"}
        memberships = {("north", "alice"): "manager"}
        for operation, result in [(approve_order, "approved"), (cancel_order, "cancelled")]:
            order = {"tenant": "north", "status": "pending"}
            operation(session, memberships, order)
            self.assertEqual(order["status"], result)
            other = {"tenant": "south", "status": "pending"}
            with self.assertRaises(PermissionError):
                operation(session, memberships, other)
            self.assertEqual(other["status"], "pending")

    def test_same_session_after_revocation(self):
        session = {"subject": "alice", "tenant": "north", "role": "manager"}
        memberships = {("north", "alice"): "manager"}
        order = {"tenant": "north", "status": "pending"}
        approve_order(session, memberships, order)
        memberships[("north", "alice")] = "member"
        order["status"] = "pending"
        self.assertTrue(can_show_approval(session))
        approve_order(session, memberships, order)
        self.assertEqual(order["status"], "approved")
        with self.assertRaises(PermissionError):
            cancel_order(session, memberships, order)
        self.assertEqual(order["status"], "approved")


if __name__ == "__main__":
    unittest.main()
