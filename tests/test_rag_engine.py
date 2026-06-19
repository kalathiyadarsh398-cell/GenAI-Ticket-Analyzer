import unittest
from src.rag_engine import search_policy

class TestRAGEngine(unittest.TestCase):
    def test_search_policy(self):
        query = "charged twice on subscription payment"
        result = search_policy(query)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)
        self.assertIn("charge", result.lower())

if __name__ == "__main__":
    unittest.main()
