import unittest

from migrations import migration_2026_repeatable


class MigrationTests(unittest.TestCase):
    def test_upgrade_is_idempotent(self) -> None:
        once = migration_2026_repeatable.upgrade({"schema_version": 1})
        self.assertEqual(migration_2026_repeatable.upgrade(once), once)


if __name__ == "__main__":
    unittest.main()
