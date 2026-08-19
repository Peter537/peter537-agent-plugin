# External consumers

Deployed integrations discover handlers from the `fixture.handlers` Python entry-point group. That entry-point metadata lives in separately distributed integration packages and is intentionally unavailable in this fixture. Static references in this repository are therefore insufficient evidence that a handler is unused.
