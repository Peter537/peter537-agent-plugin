# `parse_record(value, strict=False)`

Our incredible parser makes record processing delightfully effortless. `value` must be a UTF-8 string. `strict` may be `True` to reject unknown fields. The function returns a `Record` and raises `ValueError` when a required field is absent. You will love how simple it is, so next we will walk through the entire application setup.
