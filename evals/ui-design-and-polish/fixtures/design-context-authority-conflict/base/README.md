# Conflicting design-authority fixture

`docs/product-design-context.md` is the approved persistent context path. The repository contains two current, equally authoritative decisions that disagree materially. Runtime or token evidence cannot reconcile product authority.

No dependency or external service is required. There is no repository check that can choose between product-council decisions.

Run the dependency-free context-contract checks from the repository root:

```text
python -B -m unittest discover -s tests -v
```

The checks enforce repository state and source integrity; they do not reconcile the conflicting decisions.
