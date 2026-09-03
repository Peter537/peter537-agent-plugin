from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class ExportResult:
    status: str


class AsyncExportResource:
    def __init__(self) -> None:
        self.is_open = False
        self.close_calls = 0

    async def acquire(self) -> None:
        if self.is_open:
            raise RuntimeError("resource is already open")
        self.is_open = True

    async def close(self) -> None:
        if not self.is_open:
            raise RuntimeError("resource is not open")
        self.close_calls += 1
        self.is_open = False


class ExportJob:
    def __init__(self) -> None:
        self.resource_acquired = asyncio.Event()
        self.child_started = asyncio.Event()
        self.resource: AsyncExportResource | None = None
        self.child_task: asyncio.Task[None] | None = None

    @property
    def has_live_owned_work(self) -> bool:
        return self.child_task is not None and not self.child_task.done()

    async def run(self, release_child: asyncio.Event) -> ExportResult:
        resource = AsyncExportResource()
        self.resource = resource
        await resource.acquire()
        self.resource_acquired.set()

        child_task = asyncio.create_task(self._write_batches(release_child))
        self.child_task = child_task
        try:
            await asyncio.shield(child_task)
        except asyncio.CancelledError:
            # The cancellation path incorrectly reports success and abandons
            # both resources that this job owns.
            return ExportResult(status="completed")

        await resource.close()
        return ExportResult(status="completed")

    async def _write_batches(self, release_child: asyncio.Event) -> None:
        self.child_started.set()
        await release_child.wait()
