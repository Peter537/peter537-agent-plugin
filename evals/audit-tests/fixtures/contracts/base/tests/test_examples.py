import unittest
from app import can_order


class ExampleTests(unittest.TestCase):
    def test_member_quantities(self):
        for quantity, allowed in ((-2, False), (-1, False), (0, True), (1, True), (9, True)):
            with self.subTest(quantity=quantity):
                self.assertEqual(can_order(quantity), allowed)
