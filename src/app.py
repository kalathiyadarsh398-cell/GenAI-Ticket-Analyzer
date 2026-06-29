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

    st.title("📊 Analytics Dashboard")

    # ── Load all data with ONE optimised JOIN query ──────────────────────────
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT
        t.ticket_id            AS "Ticket ID",
        t.submission_date      AS "Submission Date",
        t.resolution_hours,
        COALESCE(p.ai_category,  t.original_category) AS "Category",
        COALESCE(p.ai_priority,  t.original_priority) AS "Priority",
        p.ai_sentiment         AS "Sentiment",
        a.action               AS "review_action"
    FROM tickets t
    LEFT JOIN ai_predictions  p ON t.ticket_id = p.ticket_id
    LEFT JOIN agent_actions   a ON t.ticket_id = a.ticket_id
    """
    df = pd.read_sql(query, conn)
    conn.close()

    # ── Empty-state guard ────────────────────────────────────────────────────
    if df.empty:
        st.info("No ticket data available yet.")
        st.stop()

    # ── Pre-processing (all in-memory, no extra DB calls) ───────────────────
    df["Submission Date"] = pd.to_datetime(df["Submission Date"], errors="coerce")

    def _status(row):
        if pd.notnull(row["review_action"]):
            return str(row["review_action"]).capitalize()
        elif pd.notnull(row["Sentiment"]):
            return "Pending"
        return "Unprocessed"

    df["Status"] = df.apply(_status, axis=1)

    # ── KPI values ───────────────────────────────────────────────────────────
    total_tickets  = len(df)
    ai_analyzed    = int(df["Sentiment"].notnull().sum())
    agent_reviewed = int(df["review_action"].notnull().sum())
    pending_review = int((df["Status"] == "Pending").sum())
    high_priority  = int((df["Priority"].astype(str).str.lower() == "high").sum())
    avg_resp       = df["resolution_hours"].mean()
    avg_resp_str   = f"{avg_resp:.1f} hrs" if pd.notnull(avg_resp) else "N/A"

    # ── Colour palette ───────────────────────────────────────────────────────
    BLUE, GREEN, ORANGE, RED, PURPLE = (
        "#1f77b4", "#2ca02c", "#ff7f0e", "#d62728", "#9467bd"
    )
    PALETTE = [BLUE, GREEN, ORANGE, RED, PURPLE]

    # ════════════════════════════════════════════════════════════════════════
    # 1. KPI CARDS
    # ════════════════════════════════════════════════════════════════════════
    st.markdown("### 📈 Key Metrics")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("🎫 Total Tickets",    f"{total_tickets:,}")
    k2.metric("🤖 AI Analyzed",      f"{ai_analyzed:,}")
    k3.metric("🧑‍💻 Agent Reviewed",   f"{agent_reviewed:,}")
    k4.metric("⏳ Pending Review",   f"{pending_review:,}")
    k5.metric("⏱️ Avg Resolution",   avg_resp_str)
    k6.metric("🚨 High Priority",    f"{high_priority:,}")

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 2. ROW 1 — Tickets by Category | Priority Distribution
    # ════════════════════════════════════════════════════════════════════════
    col_left, col_right = st.columns(2)

    with col_left:
        cat_df = (
            df["Category"].value_counts()
            .reset_index()
            .rename(columns={"index": "Category", "Category": "Count",
                             "count": "Count"})
        )
        # value_counts already returns a frame with the right names in newer pandas
        if "Category" not in cat_df.columns or len(cat_df.columns) == 1:
            cat_df = df["Category"].value_counts().rename_axis("Category").reset_index(name="Count")

        fig_cat = px.bar(
            cat_df, x="Count", y="Category", orientation="h",
            title="🗂️ Tickets by Category",
            color_discrete_sequence=[BLUE],
        )
        fig_cat.update_layout(
            yaxis={"categoryorder": "total ascending"},
            margin=dict(l=10, r=10, t=45, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_cat.update_xaxes(showgrid=True, gridcolor="#e5e5e5")
        st.plotly_chart(fig_cat, use_container_width=True)

    with col_right:
        pri_df = df["Priority"].value_counts().rename_axis("Priority").reset_index(name="Count")
        fig_pri = px.pie(
            pri_df, values="Count", names="Priority", hole=0.45,
            title="🎯 Priority Distribution",
            color_discrete_sequence=PALETTE,
        )
        fig_pri.update_traces(textposition="inside", textinfo="percent+label")
        fig_pri.update_layout(margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig_pri, use_container_width=True)

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 3. ROW 2 — Sentiment Distribution | Tickets Over Time
    # ════════════════════════════════════════════════════════════════════════
    col_left2, col_right2 = st.columns(2)

    with col_left2:
        sent_df = (
            df["Sentiment"].dropna()
            .value_counts()
            .rename_axis("Sentiment")
            .reset_index(name="Count")
        )
        sent_color_map = {"Positive": GREEN, "Neutral": BLUE, "Negative": RED}
        fig_sent = px.pie(
            sent_df, values="Count", names="Sentiment", hole=0.45,
            title="💬 Sentiment Distribution",
            color="Sentiment", color_discrete_map=sent_color_map,
        )
        fig_sent.update_traces(textposition="inside", textinfo="percent+label")
        fig_sent.update_layout(margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(fig_sent, use_container_width=True)

    with col_right2:
        time_df = df.dropna(subset=["Submission Date"]).copy()
        time_df["Date"] = time_df["Submission Date"].dt.date
        date_df = (
            time_df["Date"]
            .value_counts()
            .rename_axis("Date")
            .reset_index(name="Tickets")
            .sort_values("Date")
        )
        fig_time = px.line(
            date_df, x="Date", y="Tickets", markers=True,
            title="📅 Tickets Over Time",
            color_discrete_sequence=[PURPLE],
        )
        fig_time.update_layout(
            margin=dict(l=10, r=10, t=45, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
        )
        fig_time.update_xaxes(showgrid=False)
        fig_time.update_yaxes(showgrid=True, gridcolor="#e5e5e5")
        st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 4. ROW 3 — Review Status (full width)
    # ════════════════════════════════════════════════════════════════════════
    status_df = (
        df["Status"]
        .value_counts()
        .rename_axis("Status")
        .reset_index(name="Count")
    )
    fig_stat = px.bar(
        status_df, x="Status", y="Count",
        title="✅ Review Status",
        color="Status",
        color_discrete_sequence=PALETTE,
        text="Count",
    )
    fig_stat.update_traces(textposition="outside")
    fig_stat.update_layout(
        margin=dict(l=10, r=10, t=45, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    fig_stat.update_yaxes(showgrid=True, gridcolor="#e5e5e5")
    st.plotly_chart(fig_stat, use_container_width=True)

    st.markdown("---")

    # ════════════════════════════════════════════════════════════════════════
    # 5. RECENT TICKETS TABLE
    # ════════════════════════════════════════════════════════════════════════
    st.subheader("🗒️ Recent Tickets")

    TABLE_COLS = ["Ticket ID", "Category", "Priority", "Sentiment", "Status", "Submission Date"]
    display_df = df[TABLE_COLS].copy()

    if pd.api.types.is_datetime64_any_dtype(display_df["Submission Date"]):
        display_df = display_df.sort_values("Submission Date", ascending=False)
        display_df["Submission Date"] = (
            display_df["Submission Date"].dt.strftime("%Y-%m-%d").fillna("N/A")
        )

    st.dataframe(display_df, use_container_width=True, hide_index=True)
