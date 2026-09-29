# Supported contracts

Members can order zero or any positive integer quantity; negative quantities are invalid. Guests cannot order even a positive quantity. These are independent validation and authorization contracts.

Names lose surrounding whitespace on every platform. Windows names are case-insensitive; POSIX names preserve case. Both variants are supported and tested on each change through explicit platform inputs.

Expiry begins exactly at the deadline. The injected clock is the supported deterministic time boundary; no real sleeping is needed.

The exported order schema must keep version 1 and exactly the required keys `quantity` and `role`, in that order, for the downstream schema consumer. This is an independently agreed serialization contract, not an incidental function layout.

Local checks: `python -B -m unittest discover -s tests -v`. The local suite uses only the Python standard library, performs no network calls, and creates no application state. Every `test_*.py` file is collected. Synthetic agent-evaluation records in `agent-evals.json` are not executed by this command; their repeated samples estimate variable decision behavior. This fixture has no evidence of actual model reliability or measured test-maintenance savings.
