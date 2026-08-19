import asyncio
import unittest

from refresh import refresh_once


class RefreshTests(unittest.IsolatedAsyncioTestCase):
    async def test_returns_fetch_result_once(self) -> None:
        calls = 0

        async def fetch() -> str:
            nonlocal calls
            calls += 1
            return "ready"

        self.assertEqual("ready", await refresh_once(fetch))
        self.assertEqual(1, calls)

    async def test_propagates_failure(self) -> None:
        async def fail() -> str:
            raise RuntimeError("fixture failure")

        with self.assertRaises(RuntimeError):
            await refresh_once(fail)

    async def test_propagates_cancellation(self) -> None:
        async def cancel() -> str:
            raise asyncio.CancelledError

        with self.assertRaises(asyncio.CancelledError):
            await refresh_once(cancel)


if __name__ == "__main__":
    unittest.main()
