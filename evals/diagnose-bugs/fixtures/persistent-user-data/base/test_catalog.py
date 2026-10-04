import sqlite3
import unittest
from catalog import old_database, refresh


class RefreshTests(unittest.TestCase):
    def test_existing_database_gets_current_catalog(self):
        connection = old_database()
        self.addCleanup(connection.close)
        refresh(connection)
        self.assertEqual(connection.execute("SELECT name FROM teams ORDER BY name").fetchall(),
                         [("North",), ("South",)])

    def test_fresh_database_gets_current_catalog(self):
        connection = sqlite3.connect(":memory:")
        self.addCleanup(connection.close)
        refresh(connection)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM teams").fetchone()[0], 2)
