import asyncio
from contextlib import suppress
from enum import Enum


class JobResult(Enum):
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CallerOwnedResource:
    def __init__(self) -> None:
        self.closed = False
        self.close_count = 0
        self.use_count = 0

    def record_use(self) -> None:
        if self.closed:
            raise RuntimeError("cannot use a closed resource")
        self.use_count += 1

    async def aclose(self) -> None:
        self.close_count += 1
        self.closed = True


class SupervisedJob:
    def __init__(self) -> None:
        self._children: set[asyncio.Task[None]] = set()
        self.child_cleanup_count = 0

    @property
    def active_child_count(self) -> int:
        return len(self._children)

    async def _work(
        self,
        resource: CallerOwnedResource,
        child_started: asyncio.Event,
        release_child: asyncio.Event,
    ) -> None:
        try:
            resource.record_use()
            child_started.set()
            await release_child.wait()
        finally:
            self.child_cleanup_count += 1

    async def run(
        self,
        resource: CallerOwnedResource,
        child_started: asyncio.Event,
        release_child: asyncio.Event,
    ) -> JobResult:
        child = asyncio.create_task(
            self._work(resource, child_started, release_child),
            name="supervised-job-child",
        )
        self._children.add(child)
        try:
            await child
        except asyncio.CancelledError:
            child.cancel()
            with suppress(asyncio.CancelledError):
                await child
            return JobResult.CANCELLED
        finally:
            if not child.done():
                child.cancel()
                with suppress(asyncio.CancelledError):
                    await child
            self._children.discard(child)
        return JobResult.COMPLETED
