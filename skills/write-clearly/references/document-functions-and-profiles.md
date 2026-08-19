# Document functions and style profiles

Classify function and profile separately. One file can contain several functions, and one voice can serve several functions.

## Documentation functions

- **Tutorial:** support learning through a complete, dependable progression. Preserve motivation, orientation, reassurance, and continuity that help a learner advance.
- **How-to:** help a capable reader complete a specific task. Keep the goal, prerequisites, actions, decisions, and expected result prominent.
- **Reference:** describe a system accurately and consistently for consultation. Prefer neutral, compact, predictable structures and separate explanation or persuasion.
- **Explanation:** build understanding of causes, relationships, constraints, or design decisions. Analogy, narrative, and longer development may be useful when accurate.

Classify mixed pages by section. Do not make a tutorial austere merely because it contains API names, or turn reference material into a tutorial because an example is useful.

## Other repository functions

- **Specification or policy:** preserve normative words, definitions, scope, exceptions, and acceptance criteria. Prefer explicit actors and testable statements.
- **Decision record or plan:** distinguish evidence, decision, assumption, alternative, risk, and future work. Keep chronology only when it explains the decision.
- **Report:** lead with the question and material result, then evidence, limits, and implications appropriate to the audience.
- **Release note or migration guide:** state who is affected, what changed, required action, compatibility, and recovery. Do not mix promotional claims into breaking-change instructions.
- **UI, error, or CLI copy:** fit the available context; say what happened, what the reader can do, and any consequence. Avoid blame and unsupported reassurance.
- **Comment or docstring:** explain contracts, invariants, non-obvious reasoning, or public behavior. Do not narrate syntax or preserve obsolete implementation history.
- **Article, brand prose, or personal nonfiction:** preserve the intended argument, energy, and author identity while removing confusion and unsupported claims.

## Style profiles

### Plain general

Use clear, direct, informative prose for a broad audience. Put the main message early, use familiar words when meaning is equal, keep paragraphs coherent, and define necessary specialized terms.

### Plain technical

Use restrained, approachable technical prose for readers who may be scanning or reading in an additional language. Lead with the answer, outcome, or action the section exists to provide. Keep terminology stable, name the responsible actor when it affects understanding, use imperative steps for reader actions, and place conditions before or close to the actions and consequences they govern. Prefer claims supported by repository evidence, define necessary unfamiliar terms, and keep rhetoric subordinate to information. Do not sacrifice a technical distinction merely to shorten the prose.

### Reference-austere

Use neutral, factual, consistent description organized around the system being described. Remove promotion, emotional framing, opinion, and explanatory digression. Retain examples that efficiently clarify use or shape.

### Voice-preserving

Use representative same-language and same-genre samples. Preserve evidenced cadence, contractions, punctuation, directness, formality, asides, humor, and endings when they serve the new text. Improve comprehension without normalizing the author into generic professional prose.

### Brand or persuasive

Use an explicit brand guide, approved terminology, and approved claims. Preserve controlled personality and emphasis, but remove fabricated proof, empty superlatives, generic trend claims, and pressure that conflicts with the reader's needs.

### Controlled technical

Use only when explicitly requested and when the controlling standard is available. Treat automated editing as assistance, not certification. Do not call work ASD-STE100-conformant, approved, or certified without the official standard and qualified review.

## Profile selection defaults

- Prefer plain technical for ordinary developer documentation unless repository style says otherwise.
- Prefer reference-austere only for genuine reference, neutral catalog, or tightly controlled descriptive material.
- Prefer voice-preserving when the author or brand identity is part of the communication goal.
- Prefer plain general for mixed business or public-service prose without a stronger authority.
- Let an explicit house style override these defaults while fidelity and safety remain controlling.
