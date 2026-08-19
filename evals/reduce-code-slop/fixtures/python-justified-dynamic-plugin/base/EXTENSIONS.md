# Extension contract

Deployments provide plugin coordinates through external entry-point metadata in the form `module:factory`. The repository cannot enumerate those modules ahead of time. Dynamic loading must remain contained in `loader.py`, and the selected factory must expose a callable `create` member.
