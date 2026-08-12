# Evidence and experiments

Use this reference to prevent plausible narratives from outrunning the available evidence.

## Evidence states

- **Observation:** directly seen in command output, runtime state, source, history, test results, or an artifact.
- **Inference:** a conclusion supported by one or more observations but not directly measured.
- **Hypothesis:** a causal mechanism that still needs a distinguishing test.
- **Unknown:** a material fact not established by available evidence.

Do not promote an inference because it sounds coherent. Do not describe a hypothesis as eliminated when only one implementation or manifestation was tested.

## Compact evidence ledger

For each meaningful experiment record:

- question or hypothesis under test;
- command, probe, or comparison without sensitive arguments;
- controlled variable and relevant fixed conditions;
- predicted observation and disconfirming result;
- compact redacted result;
- interpretation and updated confidence;
- state or artifact created and cleanup required.

Keep negative results. They reduce repeated work and make later conclusions reviewable.

## Hypothesis discipline

Generate alternatives only when ambiguity warrants them. A compiler diagnostic or debugger trace may already identify a narrow cause; forcing filler alternatives wastes effort. For a hard ambiguous defect, keep a short ranked set to reduce anchoring.

An actionable hypothesis states:

1. a specific causal mechanism;
2. why current observations make it plausible;
3. what new result should appear if it is true;
4. what result would weaken it;
5. the cheapest safe discriminating experiment;
6. experiment risk, reversibility, and possible observer effects.

Test one meaningful variable at a time. Update rankings after each result instead of defending the original favorite.

## Experiment selection

Prefer experiments with high information gain, low risk, short runtime, easy restoration, and little effect on timing or behavior. A useful probe distinguishes at least two live explanations.

- Prefer debugger or runtime inspection when it can observe the necessary state without changing behavior materially.
- Add targeted assertions or structured measurements at decision boundaries.
- Avoid broad logging, random edits, and repeated commands that do not distinguish hypotheses.
- Record when instrumentation, profiling, breakpoints, tracing, retries, or diagnostic builds can change timing, load, or code paths.
- Tag temporary probes with one task-local marker that is unlikely to collide with repository content, then search for and remove it.

## Calibrated uncertainty

Avoid progress language that implies evidence is converging when it is not. Do not claim a clue is decisive, a theory exhaustive, or an upstream component faulty without a bounded comparison that supports that statement. When results contradict the current model:

1. preserve the contradictory observation;
2. check signal validity and environment drift;
3. reopen previously weakened hypotheses when justified;
4. generate a new mechanism only when it predicts a distinguishable result;
5. state the remaining uncertainty plainly.

## Causal checkpoint

A repair is justified when the evidence supports a chain of the form:

`triggering condition -> first incorrect state or boundary -> propagation -> reported symptom`

Before editing, verify that the proposed change interrupts that chain at its source and that the planned regression guard exercises the same mechanism. If only correlation exists, continue investigation or report `INCONCLUSIVE`.
