def list_projects(principal, projects):
    if principal is None:
        raise PermissionError("Sign in required")
    return [
        {"id": project["id"], "name": project["name"]}
        for project in projects
        if project["owner_id"] == principal["id"]
        and project["tenant_id"] == principal["tenant_id"]
    ]
