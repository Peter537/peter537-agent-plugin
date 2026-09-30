"""Characterize cache-hit authorization without files or services."""
import unittest

from cache import public_labels, read_document, read_summary


class CacheBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.alice = {"subject": "alice", "tenant": "north"}
        self.bob = {"subject": "bob", "tenant": "north"}
        self.south = {"subject": "charlie", "tenant": "south"}
        self.records = {
            ("north", 7): {"owner": "alice", "body": "North private", "summary": "North summary"},
            ("south", 7): {"owner": "charlie", "body": "South private", "summary": "South summary"},
        }

    def test_private_cache_hit_crosses_boundaries(self):
        cache = {}
        with self.assertRaises(PermissionError):
            read_document(self.bob, 7, self.records, cache)
        self.assertEqual(read_document(self.alice, 7, self.records, cache), "North private")
        self.assertEqual(read_document(self.bob, 7, self.records, cache), "North private")
        self.assertEqual(read_document(self.south, 7, self.records, cache), "North private")

    def test_partitioned_summary_and_public_data(self):
        cache = {}
        self.assertEqual(read_summary(self.alice, 7, self.records, cache), "North summary")
        self.assertEqual(read_summary(self.south, 7, self.records, cache), "South summary")
        with self.assertRaises(PermissionError):
            read_summary(self.bob, 7, self.records, cache)
        self.assertEqual(read_summary(self.alice, 7, self.records, cache), "North summary")
        self.assertEqual(public_labels(), ("draft", "published"))


if __name__ == "__main__":
    unittest.main()
