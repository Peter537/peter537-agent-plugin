# Missing final record

The parser loses the final nonempty record. Supported inputs are empty/whitespace-only, one or several lines, surrounding whitespace, blank lines, and presence or absence of a final newline. Return every stripped nonempty record in order. Only this local parser and its regression tests are in scope. Run `python -B -m unittest discover -s tests -v`; no dependencies or external services are needed.
