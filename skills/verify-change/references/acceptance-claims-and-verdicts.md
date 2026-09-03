# Acceptance Claims and Verdicts

Use this reference to turn an already-completed change into a finite verification contract and to decide the final result.

## Establish authority

Use the strongest applicable source of intended behavior:

1. explicit current user acceptance criteria and preservation constraints;
2. an approved task, specification, or contract identified by the user;
3. executable public interfaces, schemas, compatibility commitments, and repository tests whose ownership is clear;
4. maintained repository documentation and examples;
5. implementation structure as evidence of current behavior, not evidence of desired behavior.

Treat inferred intent, comments, stale plans, issue discussion, and generated output as weaker evidence. Do not choose whichever source makes the change pass. If equal-authority sources conflict materially, identify the conflict and return `BLOCKED` for the affected claim rather than rewriting the contract.

## Build the claim ledger

Give each required criterion a stable ID such as `VC-001`. Record:

- concise behavior and its authority;
- target revision, component, environment, and state;
- evidence layers required to establish the behavior;
- preconditions and expected observable result;
- side effects, reset, and cleanup evidence;
- status and supporting evidence location;
- evidence limitations and unresolved conditions.

Keep claims independently decidable. Split a compound criterion when one part could pass while another fails, but do not fragment one behavior into implementation-detail assertions.

## Match claims to evidence

Classify consequential conclusions as:

- **supported:** direct evidence exercises the complete bounded claim;
- **bounded:** evidence supports a narrower statement, which must be reported at that narrower scope;
- **unresolved:** available evidence neither supports nor contradicts the claim sufficiently;
- **unsupported:** the conclusion exceeds or conflicts with the evidence.

Prefer observable outcomes over implementation shape. Exact matching is appropriate only for stable machine contracts such as exit codes, schema fields, protected literals, protocol status, archive membership, or explicit state invariants. Judge user workflows, plans, prose, and visual behavior semantically.

Evidence must be current for the frozen target. A prior run, different revision, stale process, different fixture, or neighboring environment is contextual evidence unless equivalence is independently established.

## Assign verdicts without averaging

Do not calculate a quality score or let multiple passing checks cancel one failed requirement.

- Mark a claim `VERIFIED` only when all evidence layers required by that claim are supported.
- Mark it `FAILED` when trustworthy current evidence contradicts the criterion.
- Mark it `BLOCKED` when a required layer cannot be inspected safely or its target identity cannot be established.
- Use `NOT_RUN` for a planned check that did not execute and `NOT_APPLICABLE` only with a concrete reason.

Overall `FAIL` takes precedence when any required criterion fails, even when other claims are blocked. Otherwise unresolved required evidence yields `BLOCKED`. Use `PASS` only when every required criterion is verified and final-state cleanup succeeds.

OpenAI's [skill-building guidance](https://developers.openai.com/plugins/build/skills) recommends a recognizable goal, explicit boundaries, and separate tests for activation and output. Its [installed-plugin testing guidance](https://developers.openai.com/plugins/deploy/connect-chatgpt#test-the-complete-plugin) recommends representative direct, indirect, negative, and unsupported-boundary cases. Apply those principles to this skill's maintenance evaluations; they do not replace repository acceptance evidence.
