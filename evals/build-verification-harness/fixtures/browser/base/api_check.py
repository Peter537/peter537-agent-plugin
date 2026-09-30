"""Only a supplied API-shape observation, not rendered application evidence."""

payload = {"status": "saved", "value": "synthetic"}
assert payload["status"] == "saved"
