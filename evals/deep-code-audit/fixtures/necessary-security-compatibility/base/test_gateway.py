import unittest

from gateway import Gateway, Request


class MemoryStore:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.fail_next_write = False

    def read(self, key: str) -> str | None:
        return self.values.get(key)

    def write(self, key: str, value: str) -> None:
        if self.fail_next_write:
            self.fail_next_write = False
            raise OSError("synthetic write failure")
        self.values[key] = value

    def delete(self, key: str) -> None:
        self.values.pop(key, None)


class GatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryStore()
        self.gateway = Gateway(self.store, {"fixture-user": "fixture-token"})

    def request(self, **changes: object) -> Request:
        values: dict[str, object] = {
            "version": 2,
            "principal": "fixture-user",
            "token": "fixture-token",
            "nonce": "nonce-1",
            "key": "theme",
            "value": "dark",
        }
        values.update(changes)
        return Request(**values)  # type: ignore[arg-type]

    def test_rejects_wrong_token(self) -> None:
        with self.assertRaises(PermissionError):
            self.gateway.apply(self.request(token="wrong"))

    def test_rejects_replayed_nonce(self) -> None:
        request = self.request()
        self.gateway.apply(request)
        with self.assertRaises(PermissionError):
            self.gateway.apply(request)

    def test_version_one_is_normalized(self) -> None:
        self.gateway.apply(self.request(version=1, key="legacy:theme", value=" dark "))
        self.assertEqual(self.store.values["theme"], "dark")

    def test_failed_write_does_not_consume_nonce(self) -> None:
        request = self.request()
        self.store.fail_next_write = True
        with self.assertRaises(OSError):
            self.gateway.apply(request)
        self.gateway.apply(request)
        self.assertEqual(self.store.values["theme"], "dark")


if __name__ == "__main__":
    unittest.main()
