import doctest
import unittest

import math_docs


class DocumentationTests(unittest.TestCase):
    def test_examples(self) -> None:
        failures, _ = doctest.testmod(math_docs)
        self.assertEqual(failures, 0)


if __name__ == "__main__":
    unittest.main()
