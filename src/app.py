import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.config import DB_PATH
from src.ticket_processor import process_ticket
from src.database import create_tables

create_tables()

st.set_page_config(
    page_title="GenAI Ticket Analyzer",
    layout="wide"
)

page = st.sidebar.selectbox(
    "Menu",
    ["Analyze Ticket", "Agent Copilot", "Analytics"]
)

# Analyze Ticket Page

if page == "Analyze Ticket":

    st.title("GenAI Ticket Analyzer")

    import uuid, time
    auto_id = f"T-{uuid.uuid4().hex[:6].upper()}"
    ticket_id = st.text_input("Ticket ID", auto_id)

    description = st.text_area("Ticket Description", height=150)

    if st.button("Analyze Ticket"):

        if description:

            with st.spinner("Analyzing..."):
                result, reply = process_ticket(ticket_id, description)

            st.success("Ticket Processed")

            # Show results in columns
            col1, col2, col3 = st.columns(3)
            col1.metric("Category", result.get("category", "N/A"))
            col2.metric("Priority", result.get("priority", "N/A"))
            col3.metric("Sentiment", result.get("sentiment", "N/A"))

            st.subheader("Summary")
            st.write(result.get("summary", ""))

            st.subheader("Generated Reply")
            st.write(reply)

        else:
            st.warning("Enter ticket description")



# Agent Copilot Page


elif page == "Agent Copilot":

    st.title("Agent Copilot - Review Queue")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get tickets with AI predictions but no agent review
    df = pd.read_sql("""
        SELECT t.ticket_id, t.subject, t.description,
               p.ai_category, p.ai_priority, p.ai_sentiment,
               p.ai_summary, p.ai_draft_reply
        FROM tickets t
        JOIN ai_predictions p ON t.ticket_id = p.ticket_id
        LEFT JOIN agent_actions a ON t.ticket_id = a.ticket_id
        WHERE a.ticket_id IS NULL
        LIMIT 50
    """, conn)

    conn.close()

    if df.empty:
        st.info("No tickets pending review")
    else:
        st.write(f"**{len(df)} tickets** pending review")

        for i, row in df.iterrows():

            with st.expander(f"{row['ticket_id']} - {row['ai_category']}"):

                st.write("**Issue:**", row["description"])

                col1, col2, col3 = st.columns(3)
                col1.write(f"Category: {row['ai_category']}")
                col2.write(f"Priority: {row['ai_priority']}")
                col3.write(f"Sentiment: {row['ai_sentiment']}")

                st.write("**AI Draft Reply:**")
                edited_reply = st.text_area(
                    "Edit if needed",
                    value=row["ai_draft_reply"] or "",
                    key=f"reply_{row['ticket_id']}"
                )

                col1, col2, col3 = st.columns(3)

                if col1.button("Approve", key=f"a_{row['ticket_id']}"):
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("""
                        INSERT OR REPLACE INTO agent_actions
                        (ticket_id, action, agent_reply) VALUES (?, 'approved', ?)
                    """, (row["ticket_id"], edited_reply))
                    conn.commit()
                    conn.close()
                    st.success("Approved!")
                    st.rerun()

                if col2.button("Edit & Save", key=f"e_{row['ticket_id']}"):
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("""
                        INSERT OR REPLACE INTO agent_actions
                        (ticket_id, action, agent_reply) VALUES (?, 'edited', ?)
                    """, (row["ticket_id"], edited_reply))
                    conn.commit()
                    conn.close()
                    st.success("Saved!")
                    st.rerun()

                if col3.button("Reject", key=f"r_{row['ticket_id']}"):
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute("""
                        INSERT OR REPLACE INTO agent_actions
                        (ticket_id, action, agent_reply) VALUES (?, 'rejected', '')
                    """, (row["ticket_id"],))
                    conn.commit()
                    conn.close()
                    st.warning("Rejected!")
                    st.rerun()


# Analytics Page

elif page == "Analytics":

    st.title("Analytics Dashboard")

    conn = sqlite3.connect(DB_PATH)

    # KPI row
    total = pd.read_sql("SELECT COUNT(*) as c FROM tickets", conn).iloc[0]["c"]
    analyzed = pd.read_sql("SELECT COUNT(*) as c FROM ai_predictions", conn).iloc[0]["c"]
    reviewed = pd.read_sql("SELECT COUNT(*) as c FROM agent_actions", conn).iloc[0]["c"]

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tickets", f"{total:,}")
    col2.metric("AI Analyzed", f"{analyzed:,}")
    col3.metric("Agent Reviewed", f"{reviewed:,}")

    st.markdown("---")

    # Chart: Tickets by Category
    df_cat = pd.read_sql("""
        SELECT original_category as category, COUNT(*) as count
        FROM tickets WHERE original_category IS NOT NULL
        GROUP BY original_category ORDER BY count DESC
    """, conn)

    if not df_cat.empty:
        fig = px.bar(df_cat, x="category", y="count",
                     title="Tickets by Category", color="category")
        st.plotly_chart(fig, use_container_width=True)

    # Chart: Priority Distribution
    df_pri = pd.read_sql("""
        SELECT original_priority as priority, COUNT(*) as count
        FROM tickets WHERE original_priority IS NOT NULL
        GROUP BY original_priority
    """, conn)

    if not df_pri.empty:
        fig2 = px.pie(df_pri, values="count", names="priority",
                      title="Priority Distribution")
        st.plotly_chart(fig2, use_container_width=True)

    # Recent Tickets Table
    st.subheader("Recent Tickets")
    recent = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC LIMIT 10", conn)
    st.dataframe(recent)

    conn.close()
