import unittest
from src.ai_engine import analyze_ticket, generate_reply

class TestAIEngine(unittest.TestCase):
    def test_analyze_ticket(self):
        desc = "I was charged twice for my subscription payment."
        result = analyze_ticket(desc)
        self.assertIsInstance(result, dict)
        self.assertIn("category", result)
        self.assertIn("priority", result)
        self.assertIn("sentiment", result)
        self.assertIn("summary", result)

    def test_generate_reply(self):
        desc = "I was charged twice."
        policy = "Double charges are reversed within 48 hours."
        reply = generate_reply(desc, policy)
        self.assertIsInstance(reply, str)
        self.assertTrue(len(reply) > 0)

if __name__ == "__main__":
    unittest.main()
