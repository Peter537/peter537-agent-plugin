import asyncio

from supervised_job import CallerOwnedResource, JobResult, SupervisedJob


async def verify_cancelled_operation() -> None:
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
        result = await asyncio.wait_for(operation, timeout=1.0)

        assert result is JobResult.CANCELLED
        assert supervisor.active_child_count == 0
        assert supervisor.child_cleanup_count == 1
        assert resource.use_count == 1
        assert not resource.closed
        assert resource.close_count == 0
    finally:
        if not operation.done():
            operation.cancel()
            try:
                await operation
            except asyncio.CancelledError:
                pass
        await resource.aclose()
        assert resource.closed
        assert resource.close_count == 1


async def verify_completed_operation() -> None:
    resource = CallerOwnedResource()
    supervisor = SupervisedJob()
    child_started = asyncio.Event()
    release_child = asyncio.Event()
    operation = asyncio.create_task(
        supervisor.run(resource, child_started, release_child)
    )

    try:
        await asyncio.wait_for(child_started.wait(), timeout=1.0)
        release_child.set()
        result = await asyncio.wait_for(operation, timeout=1.0)

        assert result is JobResult.COMPLETED
        assert supervisor.active_child_count == 0
        assert supervisor.child_cleanup_count == 1
        assert resource.use_count == 1
        assert not resource.closed
        assert resource.close_count == 0
    finally:
        if not operation.done():
            operation.cancel()
            try:
                await operation
            except asyncio.CancelledError:
                pass
        await resource.aclose()
        assert resource.closed
        assert resource.close_count == 1


async def main() -> None:
    await verify_cancelled_operation()
    await verify_completed_operation()


if __name__ == "__main__":
    asyncio.run(main())
