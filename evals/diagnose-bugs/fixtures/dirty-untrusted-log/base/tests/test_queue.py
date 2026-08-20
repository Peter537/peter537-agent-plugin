import unittest

from queue import next_job


class QueueTests(unittest.TestCase):
    def test_returns_first_job(self) -> None:
        self.assertEqual(next_job(["first", "second"]), "first")


if __name__ == "__main__":
    unittest.main()
