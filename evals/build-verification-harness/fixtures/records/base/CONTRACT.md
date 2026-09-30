# Record parser contract

Return every stripped nonempty record, preserving contents and order, with or without a final newline. Empty and whitespace-only input returns an empty list. Production behavior is correct; this task concerns whether the existing test proves that contract.

Use `python -B -m unittest discover -s tests -v`. Python's standard library is sufficient. Only `tests/test_records.py` is approved for permanent changes. Existing `.runtime` state and user notes are unrelated work.
