from parser import RecordError, parse_record


try:
    parse_record("private-invalid-fixture")
except RecordError as error:
    assert error.code == "invalid-record"
    assert "private-invalid-fixture" not in str(error)
else:
    raise AssertionError("invalid input was accepted")
