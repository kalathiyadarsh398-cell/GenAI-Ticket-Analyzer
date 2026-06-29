import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.config import DB_PATH
from src.ticket_processor import process_ticket
from src.database import create_tables
from src.data_loader import load_csv_if_empty

create_tables()
load_csv_if_empty()

st.set_page_config(page_title="GenAI Ticket Analyzer", layout="wide")

page = st.sidebar.selectbox("Menu", ["Analyze Ticket", "Agent Copilot", "Analytics"])


# ------------------------------------------------------------------
# Analyze Ticket
# ------------------------------------------------------------------
if page == "Analyze Ticket":

    st.title("GenAI Ticket Analyzer")

    import uuid
    ticket_id = st.text_input("Ticket ID", f"T-{uuid.uuid4().hex[:6].upper()}")
    description = st.text_area("Ticket Description", height=150)

    if st.button("Analyze Ticket"):
        if description:
            with st.spinner("Analyzing..."):
                result, reply = process_ticket(ticket_id, description)

            st.success("Ticket Processed")

            col1, col2, col3 = st.columns(3)
            col1.metric("Category", result.get("category", "N/A"))
            col2.metric("Priority", result.get("priority", "N/A"))
            col3.metric("Sentiment", result.get("sentiment", "N/A"))

            st.subheader("Summary")
            st.write(result.get("summary", ""))

            st.subheader("Generated Reply")
            st.write(reply)
        else:
            st.warning("Please enter a ticket description.")


# ------------------------------------------------------------------
# Agent Copilot
# ------------------------------------------------------------------
elif page == "Agent Copilot":

    st.title("Agent Copilot - Review Queue")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

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
        st.info("No tickets pending review.")
    else:
        st.write(f"**{len(df)} tickets** pending review")

        for _, row in df.iterrows():
            with st.expander(f"{row['ticket_id']} — {row['ai_category']}"):
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
                    conn.execute(
                        "INSERT OR REPLACE INTO agent_actions (ticket_id, action, agent_reply) VALUES (?, 'approved', ?)",
                        (row["ticket_id"], edited_reply)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Approved!")
                    st.rerun()

                if col2.button("Edit & Save", key=f"e_{row['ticket_id']}"):
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute(
                        "INSERT OR REPLACE INTO agent_actions (ticket_id, action, agent_reply) VALUES (?, 'edited', ?)",
                        (row["ticket_id"], edited_reply)
                    )
                    conn.commit()
                    conn.close()
                    st.success("Saved!")
                    st.rerun()

                if col3.button("Reject", key=f"r_{row['ticket_id']}"):
                    conn = sqlite3.connect(DB_PATH)
                    conn.execute(
                        "INSERT OR REPLACE INTO agent_actions (ticket_id, action, agent_reply) VALUES (?, 'rejected', '')",
                        (row["ticket_id"],)
                    )
                    conn.commit()
                    conn.close()
                    st.warning("Rejected!")
                    st.rerun()


# ------------------------------------------------------------------
# Analytics
# ------------------------------------------------------------------
elif page == "Analytics":

    st.title("Analytics Dashboard")

    conn = sqlite3.connect(DB_PATH)

    # Single query — uses satisfaction_score to derive Sentiment for all CSV tickets
    df = pd.read_sql("""
        SELECT
            t.ticket_id         AS "Ticket ID",
            t.submission_date   AS "Submission Date",
            t.original_category AS "Category",
            t.original_priority AS "Priority",
            t.channel           AS "Channel",
            t.resolution_hours,
            t.satisfaction_score,
            t.assigned_agent    AS "Agent",
            COALESCE(
                p.ai_sentiment,
                CASE
                    WHEN t.satisfaction_score >= 4 THEN 'Positive'
                    WHEN t.satisfaction_score = 3  THEN 'Neutral'
                    WHEN t.satisfaction_score <= 2 THEN 'Negative'
                    ELSE 'Neutral'
                END
            ) AS "Sentiment",
            COALESCE(a.action, 'Pending') AS "Status"
        FROM tickets t
        LEFT JOIN ai_predictions p ON t.ticket_id = p.ticket_id
        LEFT JOIN agent_actions  a ON t.ticket_id = a.ticket_id
    """, conn)
    conn.close()

    if df.empty:
        st.info("No ticket data available yet.")
        st.stop()

    df["Submission Date"] = pd.to_datetime(df["Submission Date"], errors="coerce")

    # KPI values
    total       = len(df)
    ai_preds    = int((df["Sentiment"].isin(["Positive", "Neutral", "Negative"]) &
                       df["satisfaction_score"].isna()).sum())  # true AI-analyzed count
    reviewed    = int((df["Status"] != "Pending").sum())
    pending     = int((df["Status"] == "Pending").sum())
    high_pri    = int((df["Priority"].astype(str).str.lower() == "high").sum())
    avg_hours   = df["resolution_hours"].mean()
    avg_label   = f"{avg_hours:.1f} hrs" if pd.notnull(avg_hours) else "N/A"
    avg_sat     = df["satisfaction_score"].mean()
    avg_sat_str = f"{avg_sat:.1f} / 5" if pd.notnull(avg_sat) else "N/A"

    # KPI row
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Tickets",    f"{total:,}")
    c2.metric("High Priority",    f"{high_pri:,}")
    c3.metric("Agent Reviewed",   f"{reviewed:,}")
    c4.metric("Pending Review",   f"{pending:,}")
    c5.metric("Avg Resolution",   avg_label)
    c6.metric("Avg Satisfaction", avg_sat_str)

    st.markdown("---")

    colors = ["#3b82f6", "#22c55e", "#f97316", "#ef4444", "#a855f7"]

    # Row 1: Tickets by Category | Priority Distribution
    col1, col2 = st.columns(2)

    with col1:
        cat_df = df["Category"].value_counts().rename_axis("Category").reset_index(name="Count")
        fig = px.bar(cat_df, x="Count", y="Category", orientation="h",
                     title="Tickets by Category", color_discrete_sequence=[colors[0]])
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=True, gridcolor="#e5e5e5")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        pri_df = df["Priority"].value_counts().rename_axis("Priority").reset_index(name="Count")
        fig = px.pie(pri_df, values="Count", names="Priority", hole=0.4,
                     title="Priority Distribution", color_discrete_sequence=colors)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Row 2: Tickets Over Time | Channel Distribution
    col3, col4 = st.columns(2)

    with col3:
        time_df = df.dropna(subset=["Submission Date"]).copy()
        time_df["Month"] = time_df["Submission Date"].dt.to_period("M").astype(str)
        date_df = time_df["Month"].value_counts().rename_axis("Month").reset_index(name="Tickets").sort_values("Month")
        fig = px.line(date_df, x="Month", y="Tickets", markers=True,
                      title="Tickets Over Time (Monthly)", color_discrete_sequence=[colors[4]])
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=False, tickangle=45)
        fig.update_yaxes(showgrid=True, gridcolor="#e5e5e5")
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        chan_df = df["Channel"].value_counts().rename_axis("Channel").reset_index(name="Count")
        fig = px.pie(chan_df, values="Count", names="Channel", hole=0.4,
                     title="Tickets by Channel", color_discrete_sequence=colors)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Row 3: Avg Resolution Time by Category | Satisfaction Score Distribution
    col5, col6 = st.columns(2)

    with col5:
        res_df = (
            df.groupby("Category")["resolution_hours"]
            .mean()
            .round(1)
            .reset_index()
            .rename(columns={"resolution_hours": "Avg Hours"})
            .sort_values("Avg Hours", ascending=False)
        )
        fig = px.bar(res_df, x="Avg Hours", y="Category", orientation="h",
                     title="Avg Resolution Time by Category (hrs)",
                     color_discrete_sequence=[colors[2]])
        fig.update_layout(yaxis={"categoryorder": "total ascending"},
                          margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(showgrid=True, gridcolor="#e5e5e5")
        st.plotly_chart(fig, use_container_width=True)

    with col6:
        sat_df = (
            df["satisfaction_score"].dropna().astype(int)
            .value_counts().sort_index()
            .rename_axis("Score").reset_index(name="Count")
        )
        sat_df["Score"] = sat_df["Score"].astype(str)
        fig = px.bar(sat_df, x="Score", y="Count",
                     title="Satisfaction Score Distribution",
                     color="Score", color_discrete_sequence=colors, text="Count")
        fig.update_traces(textposition="outside")
        fig.update_layout(margin=dict(l=10, r=10, t=40, b=10),
                          plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
        fig.update_yaxes(showgrid=True, gridcolor="#e5e5e5")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Recent Tickets Table
    st.subheader("Recent Tickets")
    cols = ["Ticket ID", "Category", "Priority", "Channel", "Sentiment", "Status", "Submission Date"]
    display = df[cols].copy()
    if pd.api.types.is_datetime64_any_dtype(display["Submission Date"]):
        display = display.sort_values("Submission Date", ascending=False)
        display["Submission Date"] = display["Submission Date"].dt.strftime("%Y-%m-%d").fillna("N/A")
    st.dataframe(display.head(500), use_container_width=True, hide_index=True)
