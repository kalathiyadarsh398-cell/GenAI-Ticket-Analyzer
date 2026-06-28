import sqlite3
from src.config import DB_PATH
from src.ai_engine import analyze_ticket, generate_reply
from src.rag_engine import search_policy


def process_ticket(ticket_id, description):
    print("Processing Ticket:", ticket_id)

    # Analyze ticket using Gemini
    result = analyze_ticket(description)

    # Search matching policy
    policy = search_policy(description)

    # Generate support reply
    reply = generate_reply(description, policy)

    # Save result to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Ensure a ticket row exists so Analytics and Agent Copilot can find it
    cursor.execute("""
    INSERT OR IGNORE INTO tickets
        (ticket_id, description, submission_date, source)
    VALUES (?, ?, datetime('now'), 'ui')
    """, (ticket_id, description))

    cursor.execute("""
    INSERT OR REPLACE INTO ai_predictions
    (
        ticket_id,
        ai_category,
        ai_priority,
        ai_sentiment,
        ai_summary,
        ai_draft_reply
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        ticket_id,
        result.get("category", "General Inquiry"),
        result.get("priority", "Low"),
        result.get("sentiment", "Neutral"),
        result.get("summary", ""),
        reply
    ))

    conn.commit()
    conn.close()

    print("Ticket Processed Successfully")

    return result, reply


if __name__ == "__main__":

    ticket_id = "T001"

    description = """
    I was charged twice for my subscription payment.
    """

    result, reply = process_ticket(
        ticket_id,
        description
    )

    print("\nTicket Analysis")
    print(result)

    print("\nGenerated Reply")
    print(reply)
