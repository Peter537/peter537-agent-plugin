import unittest

import service


class ServiceTests(unittest.TestCase):
    def test_retry_contract(self) -> None:
        self.assertEqual(service.RETRY_ATTEMPTS, 3)


if __name__ == "__main__":
    unittest.main()
