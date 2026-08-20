import unittest

import session_cache


class OrderingTests(unittest.TestCase):
    def test_a_first_user(self) -> None:
        self.assertEqual(session_cache.begin_session("alpha"), "alpha")

    def test_b_second_user_is_isolated(self) -> None:
        self.assertEqual(session_cache.begin_session("beta"), "beta")


if __name__ == "__main__":
    unittest.main()
