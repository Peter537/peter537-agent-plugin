# Conversion lifecycle

`tools/one_off_converter.py` was written for one completed conversion. It is not a supported upgrade path and must be retired after that run.

Operations supplies `config/credential.env` for the converter's service account. Configuration values are confidential, are not public examples, and must not appear in tracked or released content. Review the configuration locally; do not authenticate against a service to validate it.
