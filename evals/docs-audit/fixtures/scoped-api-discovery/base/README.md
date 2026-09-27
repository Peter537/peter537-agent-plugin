# Utility repository

The rounding and request-option modules are independent of the export and administration modules. Each has a focused standard-library test.

Focused checks: `python -B -m unittest test_rounding -v` and `python -B -m unittest test_library -v` when that module exists.

Full suite: `python -B -m unittest discover -v`.
