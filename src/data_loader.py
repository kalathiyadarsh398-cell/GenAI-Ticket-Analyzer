import pandas as pd
import sqlite3
import os
from src.config import DB_PATH


def load_data():
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "customer_support_tickets.csv")
    df = pd.read_csv(csv_path)

    df = df.rename(columns={
        "Ticket_ID": "ticket_id",
        "Customer_Name": "customer_name",
        "Customer_Email": "customer_email",
        "Ticket_Subject": "subject",
        "Ticket_Description": "description",
        "Issue_Category": "original_category",
        "Priority_Level": "original_priority",
        "Ticket_Channel": "channel",
        "Submission_Date": "submission_date",
        "Resolution_Time_Hours": "resolution_hours",
        "Assigned_Agent": "assigned_agent",
        "Satisfaction_Score": "satisfaction_score"
    })

    df["source"] = "csv"

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("tickets", conn, if_exists="append", index=False)
    conn.close()

    print("Data loaded successfully")


def load_csv_if_empty():
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    conn.close()

    if count == 0:
        print("No tickets found — loading CSV...")
        load_data()
    else:
        print(f"Tickets already loaded: {count} rows")


if __name__ == "__main__":
    load_data()