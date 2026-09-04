# Event-delivery architecture

Operators need to know when an accepted event becomes durable and whether a notification failure can discard the stored event.

An event is accepted only after validation and a durable queue write. A worker later persists the event, creates the outbox entry, and then completes the queue entry. Notification delivery runs separately. If delivery fails, the stored event and pending outbox entry remain; the failure does not roll back the durable event.

```mermaid
sequenceDiagram
    accTitle: Durable event delivery and notification isolation
    accDescr: The API validates an event before durable queueing. A worker stores it before creating an outbox entry. Notification delivery occurs separately, and failure leaves both the stored event and pending outbox entry intact.
    participant Client
    participant API as Submission API
    participant Queue as Durable Queue
    participant Worker
    participant Store as Durable Store
    participant Outbox
    participant Dispatcher
    participant Notifier
    Client->>API: Submit event
    API->>API: Validate event
    API->>Queue: Enqueue accepted event
    API-->>Client: Accept after durable enqueue
    Worker->>Queue: Read queued event
    Worker->>Store: Persist event
    Worker->>Outbox: Append notification
    Worker->>Queue: Complete queue entry
    Dispatcher->>Outbox: Read pending notification
    Dispatcher->>Notifier: Attempt delivery
    alt Delivery succeeds
        Notifier-->>Dispatcher: Delivery succeeds
        Dispatcher->>Outbox: Remove sent entry
    else Delivery fails
        Notifier-->>Dispatcher: Delivery fails
        Note over Store,Outbox: Stored event and pending outbox entry remain
    end
```

The diagram describes component responsibilities and ordering. Its source and nearby text can be inspected offline, but rendered layout and accessibility behavior require a compatible Mermaid renderer.
