import unittest
import sqlite3
from src.config import DB_PATH
from src.database import create_tables

class TestDatabase(unittest.TestCase):
    def setUp(self):
        create_tables()

    def test_tables_exist(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.assertIn("tickets", tables)
        self.assertIn("ai_predictions", tables)
        self.assertIn("agent_actions", tables)

if __name__ == "__main__":
    unittest.main()
