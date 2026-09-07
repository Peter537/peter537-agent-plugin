# Mermaid Evidence and Validation

Use this reference when reviewing an existing diagram or adding one that answers a material reader question.

- Before arranging the visual, extract the relevant nodes, relationships, order, and states and trace them to repository evidence. Before changing a stale diagram, run and record an existing semantic or static check when one is available; otherwise record the exact evidenced mismatch. After editing, rerun the same check or re-evaluate the same evidence, and report both the before and after result. Keep every claim bounded to that evidence; do not present a possible recovery path as a supported operational guarantee.
- Select the form and level of abstraction from the reader question, then use the smallest useful form: a flowchart for boundaries or data flow, a sequence diagram for interactions, a state diagram for lifecycle behavior, or an entity relationship diagram for evidenced data relationships.
- Use fenced `mermaid` blocks compatible with the intended renderer. Use stable identifiers, descriptive labels, and renderer-supported accessible title and description metadata; quote labels containing punctuation, keep diagrams readable at normal width, and do not encode meaning through color alone.
- Add nearby prose that provides a textual equivalent of the diagram's essential purpose, boundaries, order, and relationships so the document remains understandable without the rendered graphic.
- Keep semantic or static evidence, Markdown structure, Mermaid syntax, rendered legibility and accessibility, and runtime behavior as separate evidence layers. A valid source block, rendered diagram, or screenshot proves only its own layer and does not prove runtime behavior.
- Validate syntax and rendering with existing project tooling when available. If a compatible renderer is unavailable, report syntax, rendering, legibility, and accessibility as unverified as applicable; do not install tooling or add a documentation platform merely to render the diagram.

