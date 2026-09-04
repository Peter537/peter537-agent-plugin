# Event Delivery Service

The service accepts validated events for durable background processing and delivers notifications separately.

See the [event-delivery architecture](docs/architecture.md) for component relationships, ordering, and failure behavior.

Run `python -B -m unittest -v` to verify the implementation and `python -B verify_docs.py` to check the documented relationship contract. This repository does not include a Mermaid renderer.
