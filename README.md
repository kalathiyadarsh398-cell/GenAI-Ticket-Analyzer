# 🤖 GenAI Ticket Analyzer

An AI-powered Customer Support Triage & Copilot that automatically classifies, prioritizes, and drafts responses for support tickets using Google Gemini API and RAG (Retrieval-Augmented Generation).

---

## 📌 Overview

This project processes customer support tickets through a 3-step AI pipeline:

1. **AI Classification** — Google Gemini analyzes the ticket and returns the category, priority, sentiment, and a summary.
2. **Policy Retrieval (RAG)** — ChromaDB searches a knowledge base of company policies and retrieves the most relevant document.
3. **Reply Drafting** — Gemini drafts a professional, policy-grounded email reply for an agent to review.

The entire workflow is accessible through a **Streamlit web dashboard** with three pages: ticket analysis, agent review queue, and analytics.

---

## ✨ Features

- **Real-Time Ticket Analysis** — Submit any support ticket and get instant AI classification (category, priority, sentiment, summary).
- **Retrieval-Augmented Generation (RAG)** — AI replies are grounded in company policy documents stored in a ChromaDB vector database, preventing hallucinated responses.
- **Agent Copilot Queue** — Human-in-the-Loop (HITL) interface where agents can approve, edit, or reject AI-drafted replies.
- **Interactive Analytics Dashboard** — Plotly-powered charts showing ticket distributions by category, priority breakdowns, and recent ticket logs.
- **Batch Data Loading** — ETL pipeline to load and clean 20,000 customer tickets from a Kaggle CSV dataset into SQLite.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|:---|:---|
| **Python 3.10+** | Core language |
| **Google Gemini API** | LLM for classification & reply generation |
| **ChromaDB** | Vector database for semantic policy search |
| **SQLite** | Relational database for ticket storage |
| **Streamlit** | Web dashboard UI |
| **Plotly** | Interactive data visualizations |
| **Pandas** | Data manipulation & ETL |

---

## 📂 Project Structure

```
GenAI-Ticket-Analyzer/
├── data/
│   ├── raw/
│   │   └── customer_support_tickets.csv   # Kaggle dataset (place here)
│   └── knowledge_base/
│       ├── refund_policy.md
│       ├── shipping_policy.md
│       ├── account_security.md
│       ├── technical_support.md
│       ├── billing_policy.md
│       └── fraud_policy.md
├── src/
│   ├── __init__.py
│   ├── config.py                          # Configuration & environment
│   ├── database.py                        # SQLite schema & table creation
│   ├── data_loader.py                     # CSV → SQLite ETL pipeline
│   ├── ai_engine.py                       # Gemini API classification & reply
│   ├── rag_engine.py                      # ChromaDB vector search
│   ├── ticket_processor.py                # Orchestration pipeline
│   └── app.py                             # Streamlit dashboard (3 pages)
├── tests/
│   ├── test_database.py
│   ├── test_ai_engine.py
│   └── test_rag_engine.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/kalathiyadarsh398-cell/GenAI-Ticket-Analyzer.git
cd GenAI-Ticket-Analyzer
```

### 2. Create a Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:
```text
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your free API key from [Google AI Studio](https://aistudio.google.com/).

---

## 🚀 Running the Project

### Step 1: Create Database Tables
```bash
python -m src.database
```

### Step 2: Load Dataset (Optional)
Download the [Customer Support Tickets Dataset](https://www.kaggle.com/datasets/ajverse/customer-support-tickets-crm-dataset) from Kaggle, place the CSV in `data/raw/`, then run:
```bash
python -m src.data_loader
```

### Step 3: Start the Dashboard
```bash
streamlit run src/app.py
```

Open your browser at **http://localhost:8501**

---

## 📸 Screenshots

*Screenshots will be added after deployment.*

<!-- 
![Analyze Ticket](screenshots/analyze.png)
![Agent Copilot](screenshots/copilot.png)
![Analytics Dashboard](screenshots/analytics.png)
-->

---

## 🔮 Future Improvements

- Auto-generate Ticket IDs for live manual submissions
- Bulk CSV upload and batch analysis from the dashboard
- AI accuracy benchmarking with confusion matrix visualization
- Email notification integration for high-priority tickets
- Multi-language ticket support

---

## ✍️ Author

**Darsh Kalathiya**

- GitHub: [github.com/kalathiyadarsh398-cell](https://github.com/kalathiyadarsh398-cell)
- LinkedIn: [linkedin.com/in/darsh-kalathiya](https://linkedin.com/in/darsh-kalathiya)
