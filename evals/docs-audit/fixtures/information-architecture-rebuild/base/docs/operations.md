# Operations

The worker retries failed requests four times.

If the checkpoint file is damaged, stop the worker, copy `state/checkpoint.backup` to `state/checkpoint.json`, and restart the worker. Do not delete the backup before the recovered checkpoint is accepted.
