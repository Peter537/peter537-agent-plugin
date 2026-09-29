import unittest
from unittest.mock import Mock

from app import can_order, expired, normalize_name


class ContractTests(unittest.TestCase):
    def test_quantity(self):
        for quantity, allowed in ((-2, False), (-1, False), (0, True), (1, True), (9, True)):
            with self.subTest(quantity=quantity):
                self.assertEqual(can_order(quantity), allowed)

    def test_guest_is_denied(self):
        self.assertFalse(can_order(1, "guest"))

    def test_windows_name(self):
        self.assertEqual(normalize_name("  Acme  ", "windows"), "acme")

    def test_posix_name(self):
        self.assertEqual(normalize_name("  Acme  ", "posix"), "Acme")

    def test_expiry_boundary(self):
        clock = Mock(side_effect=[9, 10, 11])
        self.assertFalse(expired(10, clock))
        self.assertTrue(expired(10, clock))
        self.assertTrue(expired(10, clock))
