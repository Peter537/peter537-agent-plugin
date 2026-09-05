def ordered_routes(routes):
    return tuple(sorted(routes, key=lambda route: route["queue_position"]))


def can_assign(permission, confirmed):
    return permission == "assign" and confirmed
