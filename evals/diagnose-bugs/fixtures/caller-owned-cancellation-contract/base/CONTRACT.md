# Supervised job cancellation contract

`SupervisedJob.run` is an application boundary. When its caller cancels the operation, the boundary intentionally translates that cancellation into `JobResult.CANCELLED`.

The supervisor owns the child task it creates. Before returning, it must cancel and await that child so that no internally owned task remains active.

The `CallerOwnedResource` argument is borrowed. The supervisor may use it, but must not close it. The caller that created the resource remains responsible for closing it exactly once after the supervised operation ends.

Normal completion returns `JobResult.COMPLETED` under the same ownership rules.

The repository tests contain obsolete expectations from an earlier contract. Diagnose the disagreement without changing implementation or tests.
