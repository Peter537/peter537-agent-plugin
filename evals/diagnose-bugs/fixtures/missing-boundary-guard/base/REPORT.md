# Missing record without a final newline

Calling parse_records with `alpha\nbeta` loses beta, although the same text with a final newline works. Return every stripped nonempty record in order, with or without a final newline. Preserve blank-line handling. Only this local parser and its regression tests are in scope. Run `python -B -m unittest discover -s tests -v`; no dependencies or external services are needed.
