import pandas as pd
import sqlite3
from src.config import DB_PATH

def load_data():

    df = pd.read_csv("data/raw/customer_support_tickets.csv")

    print(df.head())
    print(df.shape)

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

    print("Data Loaded Successfully")

if __name__ == "__main__":
    load_data()