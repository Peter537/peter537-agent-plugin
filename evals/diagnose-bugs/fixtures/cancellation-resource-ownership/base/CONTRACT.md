# Export job ownership contract

`ExportJob` owns the async resource and child task that it creates for one run.

On normal completion, the job returns `completed`, the child task has finished, and the resource has been closed exactly once.

When the caller cancels the job after both the resource and child task have started, cancellation must propagate as `asyncio.CancelledError`. Before propagation completes, the job must cancel and await its child task and close its resource exactly once. No job-owned work may remain alive.

The caller owns the request to cancel. It does not own cleanup of the job's child task or resource. A bounded test timeout may detect a hang, but elapsed time, sleeps, retries, and scheduler luck are not evidence of the causal behavior.

The authorized repair surface is `export_job.py` and `tests/test_export_job.py`. Preserve normal completion and the event-controlled test schedule.
