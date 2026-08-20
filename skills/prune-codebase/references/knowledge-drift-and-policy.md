# Knowledge Drift and Policy

Use this reference only when multiple repository locations appear to encode the same rule, value, mapping, schema, or lifecycle knowledge. Repetition is not itself evidence that any copy should be removed.

## Identify the knowledge, not just matching text

First state the rule in behavioral terms and identify its authority. Examples include an allowed-state transition, role-to-permission mapping, protocol code, product limit, feature eligibility rule, schema field set, retention period, or compatibility mapping.

Then determine whether each occurrence is:

- an authoritative definition;
- a derived representation generated or validated from that definition;
- a consumer that must repeat a protocol or public contract literally;
- an independent rule in another bounded context that currently has the same value;
- a test oracle or fixture intentionally separate from the implementation;
- explanatory documentation;
- a stale or conflicting copy.

Text equality does not establish shared authority. Different text can encode the same policy, while identical literals can have independent meanings.

## Demonstrate a drift mechanism

Accept a pruning or consolidation candidate only when evidence shows all of the following:

1. The occurrences represent one rule with one change owner.
2. A plausible change can update one occurrence while leaving another active.
3. That divergence produces a concrete correctness, security, compatibility, operational, or maintenance consequence.
4. One behaviorally complete source or derivation path can serve every affected consumer without creating a worse dependency or trust boundary.
5. Existing verification can detect incorrect derivation or consumption.

Useful evidence includes contradictory current values, history showing partial updates, issues caused by divergence, duplicated change sequences, generated artifacts without a validated source, or separate tests that unknowingly assert different policies.

Reject candidates based only on repeated small literals, coincidental thresholds, language or framework ceremony, test independence, protocol requirements, or a general preference for "DRY" code.

## Choose the correct remedy

The smallest credible remedy may be:

- remove a stale copy;
- generate a derived representation from the authoritative source;
- expose one typed contract to consumers inside the same ownership boundary;
- add a consistency check while preserving intentionally separate representations;
- document ownership and leave the copies independent;
- narrow a shared abstraction that incorrectly couples unrelated policies;
- keep the current structure because consolidation would transfer complexity or cross a security, deployment, or compatibility boundary.

Do not centralize secrets, environment-specific values, independently deployable configuration, client and server trust decisions, or protocol fixtures merely to reduce repetition. Do not make runtime availability depend on a build-time or remote source unless that dependency is an evidenced requirement.

## Classify uncertainty honestly

- Use `ready` when one occurrence is demonstrably stale or a safe existing authoritative derivation already exists.
- Use `needs-decision` when ownership, intended coupling, or future change policy is a product or architecture choice.
- Use `keep` when duplication is intentional, required, or safer than the proposed coupling.
- Use `research-gated` when external schemas, generated inputs, deploy boundaries, or ownership evidence are unavailable.

Record what behavior must remain stable, which knowledge source is authoritative, which consumers were checked, how drift will be prevented, and what complexity the remedy moves elsewhere.

## Primary references

Accessed 2026-08-20.

- [IETF BCP 14 terminology](https://www.rfc-editor.org/info/bcp14) provides the canonical meaning of normative requirement terms when duplicated policy includes protocol requirements.
- [JSON Schema core specification](https://json-schema.org/draft/2020-12/json-schema-core) distinguishes schemas and vocabularies that may act as machine-readable sources from their consumers.
- [Protocol Buffers language guide](https://protobuf.dev/programming-guides/proto3/) documents generated contracts, field-number compatibility, and cases where repeated generated representations must be governed by their schema rather than edited independently.
