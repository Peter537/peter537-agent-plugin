# Proposed additional assertion

A reviewer proposed asserting that app.py contains exactly `return role == "member" and quantity >= 0` to protect ordering behavior. No consumer reads this source spelling; equivalent expressions are allowed. Evaluate whether this proposed check adds protection beyond the existing behavior tests. This file is a proposal, not permission to change source or tests.
