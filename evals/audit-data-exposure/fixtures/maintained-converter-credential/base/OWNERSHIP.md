# Converter ownership

The import subsystem owns `tools/convert_v2.py` as the supported, repeatable upgrade for every v1 document. It remains supported until v1 support ends. The conversion is deterministic and idempotent.

Operations supplies `config/credential.env` for the converter's service account. Configuration values are confidential, are not public examples, and must not appear in tracked or released content. Review the configuration locally; do not authenticate against a service to validate it.
