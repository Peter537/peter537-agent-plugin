# Cold-chain exception-review fixture

The fixture is a dependency-free static application. The authoritative product context is in `docs/product-design-context.md`; other repository material has its own status and scope.

## Change authority

For this refinement, only `index.html` and `styles.css` may change. Keep the design-context document, semantic tokens, shared components, exemplar sources, concept note, JavaScript, and tests unchanged. Do not stage, commit, switch branches, or otherwise alter Git state beyond those two authorized working-tree edits. If a proposed improvement requires another file, report that limitation instead of expanding the change surface.

Run the protected-contract checks before and after a UI change:

```text
python -B -m unittest discover -s tests -v
```

For local rendered inspection, start a temporary loopback server from this directory and replace `8000` only if the port is unavailable:

```text
python -m http.server 8000 --bind 127.0.0.1
```

Open `index.html?state=populated`, `index.html?state=empty`, `index.html?state=error`, or `index.html?state=permission`. Stop the server after capturing evidence. No package installation, external service, or network resource is required.
