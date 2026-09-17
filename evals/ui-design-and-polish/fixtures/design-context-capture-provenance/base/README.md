# Capture provenance fixture

`docs/product-design-context.md` is the existing authoritative design-context path. Only that file is authorized to change.

The files in `design/` are supplied evidence records. Original screenshot and video media are absent; the records support provenance reconciliation, not direct visual interpretation. Use their observations only at that evidence level. No application startup or media acquisition is necessary.

Run the dependency-free boundary checks from the repository root:

```text
python -B -m unittest discover -s tests -v
```

These checks cover repository boundaries, local links, and canonical token ownership. They do not judge the context's meaning or prove rendered behavior.
