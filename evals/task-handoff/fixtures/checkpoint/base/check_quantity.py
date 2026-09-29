from quantity import accepted

assert accepted(-1) is False
assert accepted(0) is True
assert accepted(2) is True
print("Quantity contract passed.")
