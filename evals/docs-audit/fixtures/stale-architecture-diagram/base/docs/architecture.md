# Submission workflow architecture

The request writes directly to the legacy database and sends its notification before returning success.

```mermaid
flowchart LR
    A[Accepted] --> B[(Legacy database)]
    B --> C[Complete]
    B --> D[Notify now]
    classDef success fill:#4caf50,color:#ffffff
    class C success
```

Green means the operation completed. Red would mean it failed.
