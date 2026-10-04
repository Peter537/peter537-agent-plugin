import sqlite3
import unittest
from search import search


class SearchTests(unittest.TestCase):
    def test_empty_search_returns_nothing(self):
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        self.assertEqual(search(connection, ""), [])
