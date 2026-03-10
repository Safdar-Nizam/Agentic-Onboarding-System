# 🤖 AI New-Employee Onboarding Agent

> A production-grade **LangGraph multi-agent system** that fully automates employee onboarding — from Google Sheet intake to welcome emails, Zoom orientation, IT provisioning, and real-time status tracking.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-green.svg)](https://github.com/langchain-ai/langgraph)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991.svg)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## ⚡ Fastest Setup — Let AI Do Everything For You

**Clone this repo, open [Antigravity](https://antigravity.dev) (a free AI coding agent), choose Claude Opus 4.5 or above, and paste this prompt:**

> ✨ **Pro tip:** This was built entirely using Antigravity with Claude. Using it for setup means the AI can see your browser, navigate websites, fill in credentials, and configure everything automatically — no manual steps needed.

```
I have cloned the AI New-Employee Onboarding Agent project and I need you to set it up completely so I can run it. Here is what needs to happen:

1. Install Python dependencies from requirements.txt
2. Help me create a .env file by guiding me through getting each API key:
   - OpenAI API key (from platform.openai.com) — I need billing enabled
   - Google Cloud project: create one, enable Sheets + Gmail APIs, create a service account and download the JSON key as service_account.json, create an OAuth 2.0 Desktop Client and download as credentials.json
   - Zoom Server-to-Server OAuth app from marketplace.zoom.us — get Account ID, Client ID, Client Secret
   - Supabase project (free tier at supabase.com) — get the PostgreSQL connection string
3. Create the Google Sheet using this template: columns A-J = Employee Name, Employee Email, Role, Department, Start Date, Manager, Location, Employment Type, Onboarding Status, Processed — then share it with the service account email
4. Run db/schema.sql against my Supabase PostgreSQL database to create the tables and seed laptop inventory
5. Complete the one-time Gmail OAuth flow so token.json is created
6. Run python main.py --demo to verify everything works end-to-end

Please do each step interactively, using the browser to navigate websites and set things up where possible. Check my work at each stage before moving on.
```

After the demo runs successfully, you'll see a real welcome email in your inbox, a real Zoom meeting link, and all the data in your database.

---



## ✨ What It Does

When HR adds a new hire row to a **Google Sheet**, this system automatically:

1. 🤖 **Classifies** the role using GPT-4o-mini (Engineering, Marketing, Finance, HR, Sales…)
2. 📋 **Generates** a tailored onboarding task checklist (12–15 role-specific tasks)
3. ⚙️ **Provisions** IT resources — creates employee ID, assigns laptop from inventory
4. 📅 **Schedules** a Zoom orientation meeting and returns a real join link
5. 📧 **Sends** a GPT-written personalised welcome email via Gmail
6. ✅ **Updates** the Google Sheet column and PostgreSQL database with final status

All orchestrated by a **LangGraph StateGraph** with automatic error handling, retries, and conditional routing.

---

## 🏗️ LangGraph Architecture

![LangGraph Architecture](docs/architecture.png)

### How It Works — Node by Node

The system is a **directed acyclic graph** (DAG) built with LangGraph's `StateGraph`. A shared `OnboardingState` TypedDict is passed between every node, accumulating results as it flows through:

```
Google Sheet (Trigger)
        │
        ▼
┌──────────────────────────────────────────────────────────┐
│              LangGraph StateGraph Orchestrator            │
│                                                          │
│  [1] role_classifier ──▶ [2] onboarding_planner          │
│                                   │                      │
│                                   ▼                      │
│                      [3] resource_provisioning            │
│                                   │                      │
│                     ┌─────────────┴──────────┐           │
│                     ▼                        ▼           │
│             [4] scheduling_agent   [5] communication_agent│
│                     │                        │           │
│                     └──────────┬─────────────┘           │
│                                ▼                         │
│                      [6] status_updater                  │
└──────────────────────────────────────────────────────────┘
        │                           │
        ▼                           ▼
   Google Sheet                PostgreSQL
   (Status Updated)             (Persisted)
```

| Node | Agent | What It Does | APIs Used |
|------|-------|--------------|-----------|
| 1 | **Role Classifier** | LLM reads role + department, outputs `role_type` and required `resources` | OpenAI GPT-4o-mini |
| 2 | **Onboarding Planner** | LLM generates 12–15 role-specific onboarding tasks as structured JSON | OpenAI GPT-4o-mini |
| 3 | **Resource Provisioning** | Creates employee record, assigns next available laptop, writes tasks to DB | PostgreSQL (Supabase) |
| 4 | **Scheduling Agent** | Creates a real Zoom meeting for orientation, returns join URL | Zoom Server-to-Server OAuth |
| 5 | **Communication Agent** | GPT-4o-mini composes HTML welcome email, sent via Gmail API | OpenAI + Gmail API |
| 6 | **Status Updater** | Marks all tasks complete, updates DB status, writes back to Google Sheet | PostgreSQL + Google Sheets |

### Shared State Object

Every node reads and writes to the same `OnboardingState`:

```python
class OnboardingState(TypedDict):
    employee: EmployeeRecord        # name, email, role, dept, start date
    role_type: str                  # "Engineering" | "Marketing" | "Finance" ...
    resources: List[str]            # ["GitHub", "Jira", "AWS Console"] ...
    onboarding_tasks: List[str]     # 12-15 generated task descriptions
    employee_id: str                # "EMP-7D234C63"
    laptop_id: str                  # "LPT-001"
    zoom_link: str                  # "https://us05web.zoom.us/j/..."
    email_sent: bool                # True after Gmail confirms delivery
    final_status: str               # "Completed" | "Completed with Issues"
    errors: List[str]               # Any non-fatal errors logged here
```

---

## 📁 Project Structure

```
ai-onboarding-agent/
├── main.py                    # CLI entry point — demo / poll / once
├── api.py                     # FastAPI REST service (optional)
├── workflow.py                # LangGraph StateGraph construction & compilation
├── state.py                   # Shared OnboardingState TypedDict schema
├── config.py                  # Environment config loader with validation
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── docs/
│   └── architecture.png       # LangGraph architecture diagram
│
├── agents/                    # Specialised LangGraph node implementations
│   ├── role_classifier.py     # Node 1: LLM-powered role classification
│   ├── onboarding_planner.py  # Node 2: Onboarding checklist generation
│   ├── resource_provisioning.py # Node 3: IT resource assignment (DB)
│   ├── scheduling_agent.py    # Node 4: Zoom orientation meeting creation
│   ├── communication_agent.py # Node 5: GPT-written welcome email (Gmail API)
│   └── status_updater.py      # Node 6: Final status & dashboard updates
│
├── tools/                     # External service integrations
│   ├── google_sheets.py       # Google Sheets API v4 — read rows & update status
│   ├── gmail.py               # Gmail API (OAuth 2.0) — send welcome emails
│   └── zoom.py                # Zoom Server-to-Server OAuth — create meetings
│
└── db/                        # Database layer
    ├── schema.sql             # PostgreSQL DDL + 10 laptop seed records
    └── database.py            # Connection pool & CRUD helpers
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) or PostgreSQL database
- OpenAI API key (with billing enabled)
- Google Cloud project with Gmail + Sheets APIs enabled
- Zoom Marketplace Server-to-Server OAuth app

### 1. Clone & Install

```bash
git clone https://github.com/your-username/ai-onboarding-agent.git
cd ai-onboarding-agent
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys — see full list below
```

**Required `.env` variables:**

```env
# OpenAI
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

# Google Sheets
GOOGLE_SHEETS_SPREADSHEET_ID=your-sheet-id
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json

# Gmail
GMAIL_SENDER_EMAIL=you@gmail.com
GMAIL_CREDENTIALS_FILE=credentials.json

# Zoom
ZOOM_ACCOUNT_ID=...
ZOOM_CLIENT_ID=...
ZOOM_CLIENT_SECRET=...

# PostgreSQL
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 3. Set Up Database

Using Supabase (recommended) or any PostgreSQL instance:

```bash
# Run the schema file in your Supabase SQL editor, or:
psql $DATABASE_URL -f db/schema.sql
```

This creates 3 tables (`employees`, `onboarding_tasks`, `it_inventory`) and seeds 10 laptops.

### 4. Set Up Google APIs

#### A. Create GCP Project & Enable APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/) → Create project
2. Enable **Google Sheets API** and **Gmail API**

#### B. Service Account (for Google Sheets)

1. IAM & Admin → Service Accounts → Create Service Account
2. Keys tab → Add Key → JSON → download
3. Rename to `service_account.json` → place in project root
4. **Share your Google Sheet** with the service account email (Editor permission)

#### C. OAuth 2.0 (for Gmail)

1. APIs & Services → Credentials → Create OAuth Client ID → Desktop App
2. Download JSON → rename to `credentials.json` → place in project root
3. Add your Gmail address as a **Test User** in OAuth Consent Screen → Audience
4. Run `python gmail_oauth.py` and complete the browser sign-in once (creates `token.json`)

#### D. Google Sheet Format

Create a sheet with these columns (A–J):

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| Employee Name | Employee Email | Role | Department | Start Date | Manager | Location | Employment Type | Onboarding Status | Processed |

### 5. Set Up Zoom API

1. Go to [Zoom App Marketplace](https://marketplace.zoom.us/develop/create)
2. Create a **Server-to-Server OAuth** app
3. Activate it and add the scope: `meeting:write:admin`
4. Copy **Account ID**, **Client ID**, **Client Secret** into `.env`

---

## ▶️ Running the Agent

```bash
# Demo mode — runs with a fake employee (Sarah Chen), uses ALL real APIs
python main.py --demo

# Live polling — watches your Google Sheet every 30s for new rows
python main.py

# Process once and exit
python main.py --once

# Start REST API server
uvicorn api:app --reload --port 8000
```

### Demo Output

When running `python main.py --demo`, you'll see:

```
============================================================
  🤖  AI New-Employee Onboarding Agent  v1.0.0
============================================================
  STARTING ONBOARDING — Sarah Chen
  Role: Senior Software Engineer | Dept: Engineering
============================================================
▶ Role Classification Agent  →  Engineering | Resources: GitHub, Jira, AWS...
▶ Onboarding Plan Agent      →  12 tasks generated
▶ Resource Provisioning      →  EMP-7D234C63 | LPT-001 assigned
▶ Scheduling Agent           →  Zoom meeting created — https://zoom.us/j/...
▶ Communication Agent        →  Welcome email sent (message id: 19cd5...)
▶ Status Updater             →  Database → Completed
============================================================
  ONBOARDING SUMMARY — Sarah Chen
  Employee ID  : EMP-7D234C63
  Laptop       : MacBook Pro 16" M3 (LPT-001)
  Meeting Link : https://us05web.zoom.us/j/84447220010
  Email Sent   : Yes
  Final Status : Completed
============================================================
🏁 Demo complete.  Completed in ~46 seconds
```

---

## 📡 REST API

Start with `uvicorn api:app --reload --port 8000`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check + version |
| `POST` | `/onboard` | Manually trigger onboarding for one employee |
| `GET` | `/status/{employee_id}` | Query status + all tasks for an employee |
| `GET` | `/docs` | Interactive Swagger UI |

**Example request:**
```bash
curl -X POST http://localhost:8000/onboard \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","email":"john@company.com","role":"Product Manager","department":"Product","start_date":"2026-04-01","manager":"Jane Smith","location":"Remote","employment_type":"Full-time"}'
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) — multi-agent StateGraph |
| **LLM** | OpenAI GPT-4o-mini — role classification + email writing |
| **Trigger** | Google Sheets API v4 — polls for new rows |
| **Email** | Gmail API (OAuth 2.0) — sends personalised welcome emails |
| **Meetings** | Zoom Server-to-Server OAuth — creates real orientation meetings |
| **Database** | PostgreSQL (Supabase) — employee records, tasks, IT inventory |
| **API Layer** | FastAPI + Uvicorn — optional REST service |
| **Language** | Python 3.11+ |

---

## 🔧 Troubleshooting

| Error | Fix |
|-------|-----|
| `insufficient_quota` (OpenAI) | Add billing at [platform.openai.com/billing](https://platform.openai.com/billing) |
| `invalid_client` (Zoom) | Re-check Account ID/Client ID/Secret — watch for `I` vs `l` characters |
| `credentials.json not found` | Run `python gmail_oauth.py` to complete one-time Gmail OAuth |
| `Could not deserialize key data` | Re-download `service_account.json` from GCP Console → Keys |
| Google Sheet not readable | Share sheet with service account email as Editor |
| `access_denied` (Gmail OAuth) | Add your Gmail address as a Test User in GCP OAuth Consent → Audience |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file.

---

## 📖 Further Reading

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Google Sheets API Guide](https://developers.google.com/sheets/api)
- [Zoom Server-to-Server OAuth](https://developers.zoom.us/docs/internal-apps/)
- [DOCUMENTATION.md](DOCUMENTATION.md) — deep-dive agent design and state schema
