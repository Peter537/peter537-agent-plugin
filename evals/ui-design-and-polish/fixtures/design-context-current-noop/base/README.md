# Current dispatch design-context fixture

`docs/product-design-context.md` is the approved persistent design-context path. Maintenance is limited to that file, but an accurate artifact should remain byte-identical.

Run the dependency-free behavior checks from the repository root:

```text
python -B -m unittest discover -s tests -v
```

The checks cover current queue behavior only and provide no rendered or acceptance evidence.
