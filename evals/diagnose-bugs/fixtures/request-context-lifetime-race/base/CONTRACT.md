# Request-context contract

`handle_request()` must return the identifier supplied to that invocation.

Requests may overlap. One request starting or completing must not change another request's identity, and an implementation must not serialize otherwise independent requests merely to preserve identity.

The request identifier is call-local state. No process-global reset is required between invocations.

Verification must force the relevant overlap with synchronization events. Delays, retries, and scheduler luck are not acceptable evidence.
