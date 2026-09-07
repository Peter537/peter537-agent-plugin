# Finding Classification and Reporting

Assign four separate dimensions:

- Severity: `critical`, `high`, `medium`, or `low`, based on plausible impact and exposure.
- Confidence: `high`, `medium`, or `low`, based on evidence quality and reproducibility.
- Disposition: `required`, `recommended`, `optional`, or `research-gated`.
- Implementation order: `now`, `next`, `later`, or `backlog`, based on urgency, confidence, prerequisites, effort, blast radius, migration risk, and rollout constraints.

Use `critical` for credible immediate compromise, catastrophic data loss, or a release-blocking failure requiring urgent action. Use `high` for severe exploitable security, correctness, integrity, or availability risk. Use `medium` for a material defense, reliability, performance, testability, or maintainability risk with a realistic path. Use `low` for a contained weakness or worthwhile cleanup with demonstrated value.

Use this concrete shape for every reportable finding:

```markdown
### [Finding ID] [Consequence-oriented title]

- Owning subsystem:
- Affected location:
- Introduced by current change: yes | no | unknown
- Severity:
- Confidence:
- Disposition:
- Implementation order:

#### Observation and evidence
#### Failure, exploit, or change scenario
#### Root cause
#### Smallest credible remediation
#### Trade-offs and migration
#### Verification
#### Residual uncertainty
```

For a simplicity or change-quality finding, also identify the behavior and constraints to preserve, unnecessary surface, behaviorally complete alternative, equivalence evidence, and complexity transferred elsewhere. Do not use titles such as `too much code`, `AI slop`, `not DRY`, or `too many files`.

For dependency vulnerabilities, include the package and resolved version, advisory identifier, affected and fixed ranges, source URL, access date, and known reachability or exploitability limits. Keep package presence, vulnerable version, reachable path, and demonstrated exploitability separate.

