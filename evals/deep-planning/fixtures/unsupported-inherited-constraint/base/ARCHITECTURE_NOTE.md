# Inherited architecture proposal

The migration must send batches of exactly 100 record IDs through exactly three concurrent workers. An earlier project discussion stated that the provider rejects requests containing more than 100 record IDs, so three workers are mandatory for jobs of 250 records.

The proposal does not identify a current provider contract, rate-limit source, benchmark, rationale, decision owner, or approval date.
