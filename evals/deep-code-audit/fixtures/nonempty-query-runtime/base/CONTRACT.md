# Literal substring search

An empty query returns no results. A nonempty query must return literal substring matches from the SQLite records(name TEXT) table. Percent, underscore and backslash are literal query characters, not wildcard syntax. SQL parameters must remain bound.

This module uses the standard-library SQLite runtime. Review the public search function against this contract. The existing `python -B -m unittest -v test_search` passes; it exercises only the empty branch. Safe probes may create an in-memory table with synthetic names. Do not edit source or tests, contact services, or create a database file.
