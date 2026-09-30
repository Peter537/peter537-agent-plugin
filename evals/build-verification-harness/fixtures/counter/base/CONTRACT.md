# Counter contract

Stored values must be nonnegative integers; booleans and numeric strings are invalid. A controlled file-read seam can check malformed input, but persistence requires actual files and separate processes.

The supported CLI accepts a non-negative integer, writes it to the caller-selected JSON state file, and returns the same integer from a separate process. The storage format is independently supported: exactly one JSON field named `value`. Reject a negative value without changing an existing state file.

Use Python 3 and its standard library; no package, server, credential, or browser is needed. Invoke `python -B counter.py --state <owned-file> set 37`, then `python -B counter.py --state <owned-file> show` from this repository. This proves separate-process persistence, not crash durability.

The `.runtime` tree and user notes are pre-existing user work. Never remove or overwrite them. A check may create its own uniquely named temporary directory and remove only that directory. Production code and this contract are outside test-authoring scope.
