# Unapproved design-context path fixture

The product evidence is current, but no owner has approved a persistent design-context destination. Do not create a conventional path merely because it looks familiar.

This fixture has no runtime dependency and no check that can grant missing path authority.

Run the dependency-free context-contract checks from the repository root:

```text
python -B -m unittest discover -s tests -v
```

The checks require the repository and conventional context paths to remain unchanged; they cannot grant the missing approval.
