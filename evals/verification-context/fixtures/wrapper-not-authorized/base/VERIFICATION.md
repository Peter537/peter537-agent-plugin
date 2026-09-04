# Maintained verification

Owner: Maintainers

Status: Current

Applies to: current repository

Run `python -B check_one.py` and then `python -B check_two.py` from the repository root. Both commands are direct and dependency-free. They have been discovered in the repository but have not been run for the present worktree. The first checks the input contract; the second checks output formatting. Neither proves runtime persistence or an external integration.
