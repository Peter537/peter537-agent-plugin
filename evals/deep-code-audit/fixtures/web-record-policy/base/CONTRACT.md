# Project records

This fixture models a browser client and an authenticated server endpoint. The adapter passes a verified principal to `update_project`; it does not perform record authorization. The server's database identity bypasses row-level security. Ordinary members may read and rename only their own projects. Only administrators may change ownership, tenant, or billing status.

The browser also reads the projects table directly using a publishable key. `schema.sql` is the complete policy configuration for that path. No deployment or live database is available; SQL inspection does not prove deployed policy behavior.
