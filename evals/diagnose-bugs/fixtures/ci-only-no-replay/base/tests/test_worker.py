import unittest

from worker import transform


class WorkerTests(unittest.TestCase):
    def test_transform(self) -> None:
        self.assertEqual(transform(" alpha "), "ALPHA")


if __name__ == "__main__":
    unittest.main()
