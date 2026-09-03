from __future__ import annotations

import asyncio
import contextlib
import unittest

from export_job import ExportJob


WAIT_GUARD_SECONDS = 1.0


async def clean_test_side_leaks(job: ExportJob) -> None:
    child_task = job.child_task
    if child_task is not None and not child_task.done():
        child_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await child_task

    resource = job.resource
    if resource is not None and resource.is_open:
        await resource.close()


class ExportJobTests(unittest.IsolatedAsyncioTestCase):
    async def test_normal_completion_remains_correct(self) -> None:
        job = ExportJob()
        release_child = asyncio.Event()
        run_task = asyncio.create_task(job.run(release_child))

        try:
            await asyncio.wait_for(job.resource_acquired.wait(), WAIT_GUARD_SECONDS)
            await asyncio.wait_for(job.child_started.wait(), WAIT_GUARD_SECONDS)
            release_child.set()
            result = await asyncio.wait_for(run_task, WAIT_GUARD_SECONDS)

            self.assertEqual(result.status, "completed")
            self.assertIsNotNone(job.child_task)
            self.assertTrue(job.child_task.done())
            self.assertFalse(job.has_live_owned_work)
            self.assertIsNotNone(job.resource)
            self.assertFalse(job.resource.is_open)
            self.assertEqual(job.resource.close_calls, 1)
        finally:
            if not run_task.done():
                run_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await run_task
            await clean_test_side_leaks(job)

    async def test_cancellation_propagates_and_cleans_owned_state(self) -> None:
        job = ExportJob()
        release_child = asyncio.Event()
        run_task = asyncio.create_task(job.run(release_child))
        cancellation_propagated = False
        returned_status: str | None = None
        child_resolved_before_cleanup = False
        resource_closed_before_cleanup = False
        close_calls_before_cleanup = 0

        try:
            await asyncio.wait_for(job.resource_acquired.wait(), WAIT_GUARD_SECONDS)
            await asyncio.wait_for(job.child_started.wait(), WAIT_GUARD_SECONDS)
            run_task.cancel()
            try:
                result = await asyncio.wait_for(run_task, WAIT_GUARD_SECONDS)
                returned_status = result.status
            except asyncio.CancelledError:
                cancellation_propagated = True

            self.assertIsNotNone(job.child_task)
            self.assertIsNotNone(job.resource)
            child_resolved_before_cleanup = job.child_task.done()
            resource_closed_before_cleanup = not job.resource.is_open
            close_calls_before_cleanup = job.resource.close_calls
        finally:
            if not run_task.done():
                run_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await run_task
            await clean_test_side_leaks(job)

        self.assertTrue(cancellation_propagated)
        self.assertIsNone(returned_status)
        self.assertTrue(child_resolved_before_cleanup)
        self.assertTrue(resource_closed_before_cleanup)
        self.assertEqual(close_calls_before_cleanup, 1)
        self.assertTrue(run_task.done())
        self.assertFalse(job.has_live_owned_work)
        self.assertFalse(job.resource.is_open)
        self.assertEqual(job.resource.close_calls, 1)


if __name__ == "__main__":
    unittest.main()
