# Dispatch design-context fixture

`docs/product-design-context.md` is the existing authoritative design-context path for the dispatch console. Updating that file is the only authorized mutation. Preserve all staged, unstaged, and untracked maintainer work exactly.

Run the dependency-free behavior checks from the repository root:

```text
python -B -m unittest discover -s tests -v
```

The checks cover current queue behavior only; they do not approve design decisions or prove rendered behavior.
