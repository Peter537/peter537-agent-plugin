import unittest

import app


class StorageTests(unittest.TestCase):
    def test_local_persistence(self) -> None:
        self.assertEqual(app.storage_kind(), "sqlite")
        self.assertEqual(app.DATABASE_PATH, "state/queue.sqlite3")


if __name__ == "__main__":
    unittest.main()
