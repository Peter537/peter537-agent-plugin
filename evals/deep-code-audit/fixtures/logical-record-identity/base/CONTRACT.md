# Score identity

A result is identified by (event, entrant), independently of source_id. Different sources may deliver the same result with identical points; it must contribute once. Distinct events or entrants must each contribute, even when their points are equal. Conflicting values for a logical result must be reported as unresolved, not selected arbitrarily.

source_id is a globally unique transport record identifier. A repeated source_id is a replay of the same payload. Records are synthetic dictionaries supplied by a trusted adapter; authentication, storage, malformed input and remote services are outside this fixture.

Run `python -B -m unittest -v test_scores` and safe in-memory probes. A green happy-path suite establishes only the tested inputs. This audit authorizes no edits.
