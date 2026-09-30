# Proof and lifecycle

## Choose an authentic observation

Match the observation to the contract. Inspect a structural artifact for an independent structural requirement; call the actual interface for an API promise; interact through the rendered control for a UI promise. For persistence, write through the application and read through a separate process, client, or restart only as required by the promise. Reading an in-memory object immediately after assigning it does not establish persistence.

Control dependencies that are outside the claimed boundary without mocking the behavior being proved. A fake clock can make a real deadline comparison deterministic. A fake storage implementation cannot establish that the application's real storage survives a process restart. Keep assertion expectations independent of the implementation under test.

Browser paths should use observable user interactions, resilient locators, isolated sessions, and conditions that become true when the application is ready. Follow the existing framework's appropriate waiting/assertion mechanisms. Do not add a framework or replace a real interaction with DOM presence merely because execution is unavailable. These principles draw on [Playwright's best practices](https://playwright.dev/docs/best-practices); its optional tooling and installation recommendations are not requirements here.

## Show that the proof distinguishes behavior

Choose one fault matching the claim: omit the persisted write, return the wrong field, bypass the relevant role check, or break the interaction being asserted. Do not mutate acceptance criteria. Keep the scope and temporary location authorized, preserve the exact original bytes, and bound the experiment.

1. Exercise correct behavior through the intended command.
2. Exercise the same command and assertion against the deliberate fault in disposable state. Inspect the failure reason, not only the exit code.
3. Restore the correct bytes, rerun, and verify restoration and cleanup.

When strengthening an ineffective test, show the old assertion misses the same fault that the new assertion rejects. The old green run is evidence of a gap, not a historical product incident. A change in test count, coverage, or source length alone proves no improvement. Counterexamples, property or metamorphic relations, and differential oracles are useful only when their assumptions fit the contract; no universal technique or mutation score is required.

## Own the complete lifecycle

Use a unique task-owned writable root and pass its state location explicitly. Preserve any pre-existing runtime tree or user data. Inspect recursive reset targets: ownership of a child does not authorize deleting its parent. Refuse unsafe overlap and linked paths instead of following them into unrelated state.

Start only authorized local processes, with recorded ownership, bounded timeouts, and applicable loopback binding. Confirm readiness from the correct process/endpoint, and keep failure diagnostics available before teardown. Stop only owned processes; an unrelated process on the expected port is not yours to kill.

Cleanup must run on both success and failure without masking the check's failure status. Reconfirm ownership before deleting and verify that temporary effects are gone. Preserve a deliverable explicitly requested by the user, supplied originals, and resources with uncertain ownership. Report incomplete cleanup rather than claiming a clean finish.

## Make the result independently usable

Provide the exact invocation and working directory, required installed capabilities, fixture identity and writable location, expected success/failure meaning, teardown, and the claims each observation supports. Keep credentials and raw private captures outside version control. The next verifier must be able to exercise the original contract without hidden conversation state.

Separate a passing authored check from independent product acceptance. Browser evidence does not prove native behavior; separate-process persistence does not prove crash durability; one successful run does not prove absence of a flake. Missing evidence stays missing even when another layer passes.
