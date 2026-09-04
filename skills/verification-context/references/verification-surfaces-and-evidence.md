# Verification surfaces and evidence

## Record executable knowledge

For each verification surface, record only repository-supported details:

- purpose and acceptance source;
- direct command arguments and working directory;
- target revision, artifact, platform, or build variant;
- prerequisites and readiness signal;
- environment or authentication requirement by name or role, never by value;
- deterministic fixture or data state;
- permitted side effects;
- persistence boundary and restart expectations;
- reset and cleanup procedure, owner, and limitations;
- current validation state and last-verified target.

Prefer commands already maintained by scripts, manifests, CI, or authoritative project guidance. If a command is discoverable but unrun, label it `discovered-unverified`. If only fragments exist, record the gap rather than composing a command that the repository has never established.

## Keep proof layers distinct

- **Static and build:** parsing, schema, compilation, artifact membership, and declarative contracts.
- **API:** requests, responses, authorization boundary, and server-visible state.
- **UI:** rendered availability, interaction, keyboard and accessibility behavior, responsive states, and user-visible errors.
- **Persistence:** durable state across the repository-defined restart, reload, or process boundary.
- **Operational and telemetry:** process identity, readiness, listeners, logs, metrics, traces, and cleanup.
- **Native:** device, lifecycle, packaging, platform integration, and host-specific accessibility.

OpenTelemetry distinguishes traces, metrics, and logs because each answers different operational questions; document them separately rather than treating generic “telemetry” as proof: <https://opentelemetry.io/docs/concepts/observability-primer/>.

Playwright recommends testing user-visible behavior in isolated tests. This is useful when a repository already owns a browser harness, but it does not authorize adding Playwright or make a DOM assertion equivalent to persistence or native evidence: <https://playwright.dev/docs/best-practices>.

## Make limits reusable

State the strongest claim each surface supports and a short counter-boundary. Examples:

- a build can prove compilation for one target, not a user workflow;
- a successful request can prove one API interaction, not restart durability;
- a screenshot can prove one rendered frame, not interaction;
- browser behavior cannot prove native lifecycle or packaging;
- scanner silence cannot prove the absence of a defect or exposure.

The context should let a later verifier select claim-sufficient evidence without upgrading a weaker observation into a broader conclusion.
