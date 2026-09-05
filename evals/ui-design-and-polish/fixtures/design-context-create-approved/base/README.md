# Cold-chain design-context fixture

The Cold Chain Product Council has approved `docs/product-design-context.md` as the authoritative persistent design-context path for exception review. The file does not exist yet; creating that file is the only authorized mutation.

Run the dependency-free behavior checks from the repository root:

```text
python -B -m unittest discover -s tests -v
```

These tests establish only the behavior they exercise. They do not approve design decisions or prove rendered, accessibility, or acceptance behavior.
