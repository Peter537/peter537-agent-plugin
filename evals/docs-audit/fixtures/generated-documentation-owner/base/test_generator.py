import unittest

import service
from tools.generate_api_docs import render


class GeneratorTests(unittest.TestCase):
    def test_documents_public_route(self) -> None:
        self.assertIn(f"`GET {service.STATUS_ROUTE}`", render())


if __name__ == "__main__":
    unittest.main()
