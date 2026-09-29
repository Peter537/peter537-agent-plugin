"""Supported v1-to-v2 conversion; authentication is supplied by Operations."""

SERVICE_CONFIGURATION = "config/credential.env"


def convert(document):
    return {**document, "schema_version": 2}
