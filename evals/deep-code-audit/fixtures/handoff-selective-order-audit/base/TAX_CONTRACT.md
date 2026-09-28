# Tax calculation contract

`tax.tax_cents` accepts non-negative integer cents and integer basis points. Round the exact result to the nearest integer cent, with exact half cents rounded upward. For example, 25 cents at 1000 basis points produces 3 cents; 100 cents at 1000 basis points produces 10 cents. Reject negative amounts or rates.

This supported calculation is independent of the order-summary change in CHANGE_REQUEST.md. The audit includes both contracts, but approving an order-summary repair does not authorize changing the tax calculation.
