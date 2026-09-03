import asyncio
import unittest

from run_interleaving_check import exercise_interleaving


class RequestContextTests(unittest.IsolatedAsyncioTestCase):
    async def test_overlapping_requests_keep_call_local_identity(self) -> None:
        failures = 0
        for _ in range(20):
            failures += not await exercise_interleaving()
        self.assertEqual(failures, 0, f"incorrect_results={failures}/20")


if __name__ == "__main__":
    unittest.main()
