# Evidence for test-value decisions

## Compare assertions, not execution overlap

Name the contract and the actual assertion that would reject its violation. Two tests can execute the same lines while protecting different outputs, authorization rules, failure behavior, persistence boundaries, or input partitions. An integration test may reach a line incidentally without asserting its result.

For a proposed survivor, check that it is collected and executed in the relevant job, platform, configuration, and schedule. A skipped Linux case does not replace a Windows assertion; a nightly check may not replace required per-change protection. Missing execution evidence limits the claim even if the source appears adequate.

Reconcile overlapping candidates as a set. If A relies on B and B relies on A, retain an actual survivor or consolidate their protection before removal. After consolidation, verify the named assertion still exists and observes the contract. Count reduction and unchanged line coverage do not establish this.

## Preserve justified exactness and seams

- Exact schema keys, protocol bytes, exported package membership, architecture restrictions, and migration shapes may be independent contracts. Source inspection can be the cheapest valid check; a source-string assertion that merely repeats an incidental local implementation may instead provide little protection.
- Mocks and fake clocks can control external failure or time while leaving the real behavior under test. They are weak evidence when they supply the very outcome the test claims the product produced.
- Shared fixtures, lifecycle checks, and test seams can preserve isolation or make credible faults reproducible. Do not remove production helpers merely because tests are their only visible caller during this review.
- Security-denial checks and distinct role, tenancy, input, and platform partitions remain useful even when their syntax or coverage resembles another test.
- Repeated stochastic agent evaluations may estimate reliability or cover a declared variability condition. Inspect prompts, expectations, authority, environments, and sampling intent before calling them duplicates. Never deduplicate only by similar wording, identical initial seeds, or repeated runs; also do not claim statistical adequacy without relevant evidence.

## Distinguish ineffective protection from unnecessary protection

A tautology, an expected value calculated with the function under test, or a fake that implements the claimed behavior may fail to protect a **necessary** contract. Recommend strengthening or a separate missing-verification task. Do not remove the only purported guard and claim equivalent protection.

A failing test cannot be classified by its color alone. Reconcile its assertion with independent product authority. Preserve the failing evidence and hand off diagnosis when a credible product defect remains. If the contract is obsolete, establish retirement authority separately.

## Use experiments selectively

First inspect the assertion and its execution conditions. When inspection cannot establish consequential failure detection, propose the smallest authorized, reversible experiment: one defect matching the claimed contract in a disposable copy, then run the named survivor. An import/setup failure does not demonstrate detection of the target defect. Restore the original bytes and verify the restored check passes, or preserve and report the unrelated starting failure.

Do not build a general mutation system for an audit. Do not require red-before evidence for behavior-preserving cleanup of already-correct code; comparable green runs plus evidence about retained assertions may suffice. Private source and outputs stay local, and cleanup removes only freshly verified task-owned state.
