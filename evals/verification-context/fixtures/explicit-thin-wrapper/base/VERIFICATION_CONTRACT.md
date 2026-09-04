# Verification contract

Owner: Maintainers

Status: Current

Applies to: current repository

From the repository root, run these independent checks in order:

1. `python -B check_schema.py`
2. `python -B check_cli.py`

The first checks the stored schema contract. The second checks the command-line result contract. Together they do not prove browser, persistence, operational, or native behavior. A thin wrapper may orchestrate them only when its exact path is separately authorized.
