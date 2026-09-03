# Parser rejection contract

Malformed records must raise `RecordError` with public code `invalid-record`. Raw input must not appear in the error.
