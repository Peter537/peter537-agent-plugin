# Counter CLI contract

Status: current

Owner: CLI maintainers

Scope: the current repository checkout

The Counter CLI must accept a non-negative integer, persist it to a caller-selected synthetic state file, and return the same value from a separate process. Validation must use this root command:

```text
python -B verify_contract.py
```

The check owns the complete `.runtime` tree only after proving that the tree did not exist before the run. It may create synthetic state beneath that tree and must remove exactly what it created. The check proves persistence across separate CLI processes. It does not prove machine-restart durability, filesystem crash safety, or compatibility with production data.
