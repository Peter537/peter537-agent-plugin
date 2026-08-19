import unittest

from client import fetch_identifiers


class ClientTests(unittest.TestCase):
    def test_normalizes_identifiers(self) -> None:
        self.assertEqual(["17"], fetch_identifiers(lambda: [{"id": 17}]))

    def test_current_failure_contract_is_empty(self) -> None:
        def fail() -> list[dict[str, object]]:
            raise TimeoutError("fixture timeout")

        self.assertEqual([], fetch_identifiers(fail))


if __name__ == "__main__":
    unittest.main()
