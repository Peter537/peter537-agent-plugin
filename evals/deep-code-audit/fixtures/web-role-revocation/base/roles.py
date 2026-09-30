def can_show_approval(session):
    return session is not None and session["role"] == "manager"


def approve_order(session, memberships, order):
    if session is None or session["tenant"] != order["tenant"]:
        raise PermissionError("Wrong tenant")
    if session["role"] != "manager":
        raise PermissionError("Manager required")
    order["status"] = "approved"


def cancel_order(session, memberships, order):
    if session is None or session["tenant"] != order["tenant"]:
        raise PermissionError("Wrong tenant")
    if memberships.get((session["tenant"], session["subject"])) != "manager":
        raise PermissionError("Current manager required")
    order["status"] = "cancelled"
