import pandas as pd
import sqlite3
import os
from src.config import DB_PATH


def load_csv_if_empty():
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    conn.close()

    if count == 0:
        print("No tickets found — loading CSV...")
        _load_csv()
    else:
        print(f"Tickets already loaded: {count} rows")


def _load_csv():
    # resolve path relative to this file so it works from any working directory
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(base, "data", "raw", "customer_support_tickets.csv")

    if not os.path.exists(csv_path):
        print(f"CSV not found at {csv_path}")
        return

    df = pd.read_csv(csv_path)

    df = df.rename(columns={
        "Ticket_ID":            "ticket_id",
        "Customer_Name":        "customer_name",
        "Customer_Email":       "customer_email",
        "Ticket_Subject":       "subject",
        "Ticket_Description":   "description",
        "Issue_Category":       "original_category",
        "Priority_Level":       "original_priority",
        "Ticket_Channel":       "channel",
        "Submission_Date":      "submission_date",
        "Resolution_Time_Hours":"resolution_hours",
        "Assigned_Agent":       "assigned_agent",
        "Satisfaction_Score":   "satisfaction_score",
    })

    df["source"] = "csv"

    # keep only columns that exist in the tickets table schema
    keep = [
        "ticket_id", "customer_name", "customer_email", "subject",
        "description", "original_category", "original_priority",
        "channel", "submission_date", "resolution_hours",
        "assigned_agent", "satisfaction_score", "source"
    ]
    df = df[[c for c in keep if c in df.columns]]

    conn = sqlite3.connect(DB_PATH)
    try:
        # insert row-by-row with INSERT OR IGNORE to skip duplicates safely
        df.to_sql("tickets_staging", conn, if_exists="replace", index=False)
        conn.execute("""
            INSERT OR IGNORE INTO tickets
                (ticket_id, customer_name, customer_email, subject,
                 description, original_category, original_priority,
                 channel, submission_date, resolution_hours,
                 assigned_agent, satisfaction_score, source)
            SELECT
                ticket_id, customer_name, customer_email, subject,
                description, original_category, original_priority,
                channel, submission_date, resolution_hours,
                assigned_agent, satisfaction_score, source
            FROM tickets_staging
        """)
        conn.execute("DROP TABLE IF EXISTS tickets_staging")
        conn.commit()
        print(f"Loaded {len(df)} tickets from CSV")
    except Exception as e:
        print(f"CSV load error: {e}")
    finally:
        conn.close()


def load_data():
    _load_csv()


if __name__ == "__main__":
    load_data()