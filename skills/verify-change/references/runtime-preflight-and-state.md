# Runtime Preflight and State

Read this reference before using an executable artifact, starting a process, authenticating, or changing disposable verification state.

## Identify the target exactly

Record enough information to distinguish the intended target from a nearby or stale one:

- current commit and relevant staged, unstaged, and untracked changes;
- explicit comparison base or the reason no base is needed;
- build configuration, runtime, feature flags, and environment;
- artifact origin and freshness relative to the frozen source state;
- entrypoint, process identity, listener address, and working directory;
- test data, database, cache, queue, filesystem root, or other state boundary.

Do not assume a successful start command launched the intended process. Check the process and listener independently. Do not reuse an existing listener until its ownership and artifact identity are known. If equivalence cannot be established, stop with `BLOCKED` rather than testing the wrong target.

## Check prerequisites before side effects

Confirm:

- required runtimes and repository-native commands already exist;
- the environment can be reset without damaging shared or user data;
- credentials, if explicitly authorized, have the least privilege needed;
- fixture data is deterministic, non-sensitive, and representative of the claim;
- the target is local or otherwise within the user's explicit authorization;
- ports, filenames, database names, and other resources will not collide;
- every side effect has an exact ownership test and cleanup operation.

Prefer a new disposable directory, isolated database, loopback address, and ephemeral port. Do not silently point a local application at production, a shared developer service, or the user's real records.

## Capture the starting state

Before running a side-effecting check, record only the state needed to prove restoration:

- Git status and relevant file inventory;
- task-owned process and listener inventory;
- fixture or database generation/version markers;
- expected generated-output locations;
- service state needed to distinguish pre-existing from task-created resources.

Avoid dumping environment variables, connection strings, tokens, row contents, or absolute personal paths. Use redacted identifiers and counts when they are sufficient.

## Handle common identity failures

- **Stale build:** rebuild only through an existing authorized repository command; otherwise report the stale artifact as a blocker.
- **Dirty worktree:** verify the recorded snapshot without folding unrelated changes into the claim. Preserve it byte-for-byte.
- **Missing entrypoint:** inspect repository guidance and manifests; do not invent or scaffold one.
- **Authentication failure:** distinguish an invalid product response from unavailable verification access. Do not weaken authentication or create credentials.
- **Unavailable dependency or runtime:** report the gap and route a proposed addition through `$audit-dependencies`.
- **Generated output:** record whether it is expected, compare it to the starting inventory, and remove only output created by this task.

## CI and observational targets

Tie CI evidence to the exact revision, workflow, job, matrix cell, environment, and artifact where available. A green job for a neighboring revision is not evidence for the target. Treat truncated logs, expired artifacts, missing matrix variants, and inaccessible retry history as explicit gaps.

Observational evidence can support a claim that is itself about that observation. It cannot prove a local replay, end-to-end state transition, or repaired runtime behavior that was not exercised.
