import sqlite3
from src.config import DB_PATH

def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tickets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT UNIQUE,
        customer_name TEXT,
        customer_email TEXT,
        subject TEXT,
        description TEXT,
        original_category TEXT,
        original_priority TEXT,
        channel TEXT,
        submission_date TEXT,
        resolution_hours REAL,
        assigned_agent TEXT,
        satisfaction_score INTEGER,
        source TEXT DEFAULT 'csv'
    )
    """)

    # AI predictions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT UNIQUE,
        ai_category TEXT,
        ai_priority TEXT,
        ai_sentiment TEXT,
        ai_summary TEXT,
        key_entities TEXT,
        retrieved_policy TEXT,
        ai_draft_reply TEXT,
        confidence_score REAL,
        processing_time_ms INTEGER,
        FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
    )
    """)

    # Agent actions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS agent_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id TEXT,
        action TEXT,
        agent_reply TEXT,
        reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticket_id) REFERENCES tickets(ticket_id)
    )
    """)

    conn.commit()
    conn.close()

    print("Database tables created")

if __name__ == "__main__":
    create_tables()