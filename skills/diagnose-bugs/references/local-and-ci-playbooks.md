# Local and CI playbooks

Use the applicable playbook to define specialized evidence and completion criteria. These are branches of one causal workflow, not checklists that must all run.

## Deterministic correctness defect

- Preserve the exact input, expected result, actual result, and first divergent intermediate state.
- Check empty, boundary, invalid, and neighboring cases relevant to the same invariant.
- Verify the fix at the source of incorrect state, not only at the visible failure.

## Build or compile failure

- Identify the first meaningful diagnostic rather than treating the final cascade as independent failures.
- Compare toolchain, target, generated files, conditional configuration, and environment with a working state.
- Re-run from the narrowest repository-supported clean boundary without deleting user work.
- Verify both the focused failing target and the relevant broader build graph.

## Regression

- Confirm last-known-good and first-known-bad states with the same predicate.
- Compare code, configuration, dependency, data, and environment changes; do not assume the newest code commit is causal.
- Use differential execution or bisection only after the predicate is reliable.
- Verify the repair against both anchors and the current original scenario.

## Flaky or order-dependent failure

- Record failures per attempts, run order, seed, worker count, clock, locale, load, retries, shared state, and external conditions.
- Compare isolated and suite execution, fixed and shuffled order, and controlled resource pressure as relevant.
- Preserve a failing seed, schedule, or event sequence when possible.
- A retry, delay increase, quarantine, or single green run is not a repair. Compare before-and-after rates under equivalent conditions.

## Concurrency defect

- Exercise the realistic concurrent path rather than only serial helpers.
- Use already-available race detectors, trace tools, or deterministic schedulers when the repository supports them.
- Inspect ownership, synchronization, atomicity, cancellation, lifecycle, and ordering boundaries.
- Preserve the conflicting accesses or smallest known schedule and repeat validation appropriately.

## Measured performance regression

- Define the user-visible metric, workload, baseline, threshold, warm-up, repetitions, machine conditions, and noise tolerance before profiling.
- Compare distributions or repeated samples, not one timing.
- Profile or measure resource utilization, saturation, and errors before optimizing.
- Recheck correctness and compare post-repair measurements under the same conditions.
- Route a proactive request to find general bottlenecks to an audit workflow instead of this skill.

## Integration or distributed local failure

- Trace correlation identifiers and boundary inputs/outputs across the smallest available local or CI topology.
- Compare configuration propagation, contract versions, timeouts, retries, clocks, partial failures, and dependency state.
- Replace one boundary at a time with a controlled equivalent only when that comparison remains authentic.
- Verify both sides of the contract and the end-to-end original scenario.

## Environment or dependency mismatch

- Compare runtime, architecture, locale, timezone, environment-variable presence without values, feature flags, lockfiles, generated files, system packages, and clean versus existing environments.
- Do not update a dependency merely because versions differ. Establish that the exact resolution causes the failure and coordinate with `$audit-dependencies` before changing it.
- Record unsupported or inaccessible environment differences as limits rather than assuming parity.

## Data-dependent defect

- Minimize and sanitize the failing shape while preserving schema, encoding, ordering, nulls, boundaries, and relevant historical form.
- Inspect migrations, serializers, import/export boundaries, rejected-record handling, and state transitions.
- Keep real records and sensitive artifacts local; do not turn production payloads into committed fixtures.
- Use `$audit-data-exposure` for a dedicated repository leak or anonymization review rather than expanding this diagnosis silently.

## Out-of-scope incidents

If the request concerns an active production outage, security incident, live compromise, or ongoing corruption risk, do not experiment or change production under this skill. Preserve the user's supplied evidence, avoid disclosing it, and provide a precise handoff to an authorized incident-response workflow.
