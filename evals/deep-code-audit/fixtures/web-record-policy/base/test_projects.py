"""Characterize server updates; this does not execute database policies."""
import copy
import unittest

from projects import PROJECTS, update_project


class ProjectBoundaryTests(unittest.TestCase):
    def setUp(self):
        saved = copy.deepcopy(PROJECTS)
        self.addCleanup(self.restore, saved)
        self.member = {"id": "alice", "tenant_id": "a", "role": "member"}

    def restore(self, saved):
        PROJECTS.clear()
        PROJECTS.update(saved)

    def test_owner_rename_and_anonymous_rejection(self):
        self.assertEqual(update_project(self.member, 1, {"name": "Renamed"})["name"], "Renamed")
        with self.assertRaises(PermissionError):
            update_project(None, 1, {"name": "Anonymous"})
        self.assertEqual(PROJECTS[1]["name"], "Renamed")

    def test_other_owner_same_tenant_and_other_tenant(self):
        PROJECTS[3] = {"id": 3, "owner_id": "carol", "tenant_id": "a", "name": "Peer", "billing_status": "unpaid"}
        for project_id in [3, 2]:
            self.assertEqual(update_project(self.member, project_id, {"name": "Changed"})["name"], "Changed")

    def test_member_can_change_restricted_fields(self):
        body = {"owner_id": "mallory", "tenant_id": "b", "billing_status": "paid"}
        result = update_project(self.member, 1, body)
        self.assertTrue(all(result[k] == v for k, v in body.items()))


if __name__ == "__main__":
    unittest.main()
