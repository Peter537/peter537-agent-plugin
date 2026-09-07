PROJECTS = {
    1: {"id": 1, "owner_id": "alice", "tenant_id": "a", "name": "Private", "billing_status": "unpaid"},
    2: {"id": 2, "owner_id": "bob", "tenant_id": "b", "name": "Other", "billing_status": "unpaid"},
}


def update_project(principal, project_id, body):
    if principal is None:
        raise PermissionError("Sign in required")
    project = PROJECTS[project_id]
    project.update(body)
    return dict(project)
