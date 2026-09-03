import asyncio
import unittest

from supervised_job import CallerOwnedResource, SupervisedJob


class ObsoleteCancellationContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_cancellation_propagates_from_the_boundary(self) -> None:
        resource = CallerOwnedResource()
        supervisor = SupervisedJob()
        child_started = asyncio.Event()
        release_child = asyncio.Event()
        operation = asyncio.create_task(
            supervisor.run(resource, child_started, release_child)
        )

        try:
            await asyncio.wait_for(child_started.wait(), timeout=1.0)
            operation.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await asyncio.wait_for(operation, timeout=1.0)
        finally:
            if not operation.done():
                operation.cancel()
                try:
                    await operation
                except asyncio.CancelledError:
                    pass
            await resource.aclose()
            self.assertEqual(resource.close_count, 1)

    async def test_supervisor_closes_the_borrowed_resource(self) -> None:
        resource = CallerOwnedResource()
        supervisor = SupervisedJob()
        child_started = asyncio.Event()
        release_child = asyncio.Event()
        operation = asyncio.create_task(
            supervisor.run(resource, child_started, release_child)
        )

        try:
            await asyncio.wait_for(child_started.wait(), timeout=1.0)
            operation.cancel()
            await asyncio.wait_for(operation, timeout=1.0)
            self.assertTrue(resource.closed)
        finally:
            if not operation.done():
                operation.cancel()
                try:
                    await operation
                except asyncio.CancelledError:
                    pass
            await resource.aclose()
            self.assertEqual(resource.close_count, 1)


if __name__ == "__main__":
    unittest.main()
