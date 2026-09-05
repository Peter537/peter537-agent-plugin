# Status and action contracts

`ExceptionStatus` accepts exactly `release`, `hold`, and `quarantine`. Each state presents a text label and an icon in addition to colour.

`QuarantineAction` owns confirmation, cancellation, disabled, submitting, success, and error states and preserves the `data-testid="quarantine-action"` hook.

These component names and state contracts are canonical. CSS values and DOM nesting are implementation details.
