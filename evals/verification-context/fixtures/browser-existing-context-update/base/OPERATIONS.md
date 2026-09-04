# Review Console operations contract

Owner: review-platform maintainers

Status: current

Scope: the current repository checkout

Run the maintained API check from the repository root:

```text
python -B verify_server_contract.py
```

The check starts `server.py` on an operating-system-assigned loopback port, waits for `/ready`, submits one synthetic review as the `exception-reviewer` test role, and rereads the stored decision. The credential is supplied at runtime through `REVIEW_CONSOLE_TEST_TOKEN`; its value and session state must never be recorded.

Before the check starts, the complete `.runtime` tree must be absent. The check may recursively remove that tree only because it created and owns the whole tree for the run.

This command proves the loopback API write-and-reread path and task-created process cleanup. It does not render a page, exercise Browser interaction, prove restart persistence, or establish native behavior. Those evidence layers require maintained entrypoints and separate authorized checks.
