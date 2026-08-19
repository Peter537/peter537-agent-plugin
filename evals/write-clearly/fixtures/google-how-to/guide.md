---
title: Configure Atlas Sync
---

# Configuration information for Atlas Sync

Atlas Sync v3.1 accepts only local YAML configuration. There is a configuration step that you do by running `atlas sync configure --file ./atlas.yaml`. After that operation has happened, the service reads the file when it starts. The service does not upload this file, but an administrator may separately configure remote backups.
