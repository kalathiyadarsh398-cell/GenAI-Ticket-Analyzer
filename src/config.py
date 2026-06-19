from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DB_PATH = BASE_DIR / "data" / "tickets.db"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
