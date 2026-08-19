import unittest

from protocol import ProtocolError, State, TransferSession


class TransferSessionTests(unittest.TestCase):
    def test_successful_transfer(self) -> None:
        session = TransferSession()
        session.begin_negotiation()
        session.accept_peer()
        session.begin_transfer()
        session.acknowledge_chunk()
        session.complete()
        self.assertEqual(session.state, State.COMPLETE)

    def test_recovery_returns_through_transfer_boundary(self) -> None:
        session = TransferSession(State.TRANSFERRING)
        session.lose_connection()
        session.recover()
        self.assertEqual(session.state, State.READY)
        session.begin_transfer()
        self.assertEqual(session.state, State.TRANSFERRING)

    def test_completion_without_data_is_rejected(self) -> None:
        session = TransferSession(State.TRANSFERRING)
        with self.assertRaises(ProtocolError):
            session.complete()


if __name__ == "__main__":
    unittest.main()
