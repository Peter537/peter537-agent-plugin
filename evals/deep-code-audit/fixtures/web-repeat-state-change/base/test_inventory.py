"""Characterize repeated effects and the separate scoped receipt control."""
import unittest

from inventory import release, reserve


class InventoryBoundaryTests(unittest.TestCase):
    def test_reservation_retry_and_distinct_request(self):
        principal = {"subject": "alice", "tenant": "north"}
        stock = {("north", "book"): 10}
        receipts = {}
        self.assertEqual(reserve(principal, "book", 2, "first", stock, receipts), 8)
        self.assertEqual(reserve(principal, "book", 2, "first", stock, receipts), 6)
        self.assertEqual(reserve(principal, "book", 1, "second", stock, receipts), 5)

    def test_release_receipt_scope_and_payload(self):
        alice = {"subject": "alice", "tenant": "north"}
        bob = {"subject": "bob", "tenant": "north"}
        other = {"subject": "alice", "tenant": "south"}
        stock = {("north", "book"): 0, ("south", "book"): 0}
        receipts = {}
        self.assertEqual(release(alice, "book", 2, "same", stock, receipts), 2)
        self.assertEqual(release(alice, "book", 2, "same", stock, receipts), 2)
        with self.assertRaises(ValueError):
            release(alice, "book", 3, "same", stock, receipts)
        self.assertEqual(stock[("north", "book")], 2)
        self.assertEqual(release(bob, "book", 2, "same", stock, receipts), 4)
        self.assertEqual(release(other, "book", 2, "same", stock, receipts), 2)
        self.assertEqual(release(alice, "book", 1, "next", stock, receipts), 5)


if __name__ == "__main__":
    unittest.main()
