import unittest

from library import internal_summary


class LibraryTests(unittest.TestCase):
    def test_internal_summary(self) -> None:
        self.assertEqual(internal_summary([2, 3]), 5)


if __name__ == "__main__":
    unittest.main()
