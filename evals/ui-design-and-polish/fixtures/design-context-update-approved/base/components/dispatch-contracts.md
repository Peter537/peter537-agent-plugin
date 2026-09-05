# Dispatch component contracts

`RouteRiskStatus` owns `low`, `medium`, and `high` states with text and icon semantics. `AssignmentAction` owns confirmation, pending, success, error, and permission-denied states.

The canonical hooks are `data-testid="route-risk"` and `data-testid="assign-shipment"`. CSS values and DOM nesting are not public contracts.
