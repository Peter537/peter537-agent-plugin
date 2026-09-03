# Order summary change

Add `total_cents` to each result returned by `summarize_order`. Compute the total from the values supplied to that call, preserve the existing `item_count` and negative-value validation, and keep the function deterministic and call-local.
