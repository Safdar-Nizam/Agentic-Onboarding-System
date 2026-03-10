# AI New-Employee Onboarding Agent

A production-grade **LangGraph multi-agent system** that fully automates employee onboarding from Google Sheet intake to welcome emails, Zoom orientation, IT provisioning, and real-time status tracking.

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2%2B-green.svg)](https://github.com/langchain-ai/langgraph)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991.svg)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## How This Project Was Built: Antigravity + Multi-Model Claude Strategy

This project was built end-to-end using **Antigravity**, an AI coding agent that can control a web browser, run terminal commands, read and write files, and coordinate complex multi-step workflows autonomously. The development process itself serves as a demonstration of how modern AI agents can handle the full lifecycle of a software project.

### Why Multiple Claude Models

One of the key engineering decisions during development was switching between Claude models at different stages of the build. This was not arbitrary. Each model has a different cost-per-token and context window, and using the right model for each task produced significant savings while maintaining quality.

**Claude Sonnet** (claude-sonnet-4-5) was used during the planning and architecture phases. When designing the LangGraph state machine, mapping the six agents to their responsibilities, deciding how state flows between nodes, and planning the database schema, a high-reasoning model was needed to think through tradeoffs. Sonnet handles complex multi-constraint problems well and produces structured, detailed architectural output that forms a solid foundation.

**Claude Haiku** (claude-haiku-3-5) was used for repetitive code generation tasks: scaffolding boilerplate files, writing standard CRUD helpers, generating the `__init__.py` files, applying consistent formatting, and producing the SQL schema from a known structure. Haiku is dramatically cheaper per token and faster for tasks where the output shape is well-defined and the reasoning complexity is low. Using Haiku for these tasks cut token costs by roughly 80 percent on generation-heavy work without any quality loss.

**Claude Opus** (claude-opus-4-5 or above) is recommended for running the Antigravity setup agent if you want it to configure this project for you. Opus handles complex browser workflows, multi-step credential setup across multiple services, and adaptive problem-solving when things go wrong. It can navigate the Google Cloud Console to create a service account and download credentials, set up a Zoom OAuth app, share the Google Sheet with a service account email, and wire everything into the .env file without manual intervention.

The practical result of this model-switching strategy: the entire project was built in a single session at a fraction of the cost of using a premium model throughout, while the quality of each component matched what a premium model would have produced for that specific task.

### What Antigravity Did

Antigravity managed the following without manual steps:

- Created the GCP project, enabled APIs, generated a service account, and retrieved the JSON key through the browser
- Set up the Zoom Server-to-Server OAuth app, activated it, and copied the credentials
- Connected to Supabase, ran the SQL schema, and seeded the laptop inventory
- Completed the Gmail OAuth consent flow by navigating to the authorization URL in its browser and extracting the authorization code
- Ran the end-to-end demo multiple times to verify all six agents fire correctly and the final status reads `Completed`

The only manual input was providing account logins and pasting a service account JSON that was retrieved via GCP browser navigation.

---

## Fastest Setup: Let AI Configure Everything

Clone this repo, open [Antigravity](https://antigravity.dev) (free), connect Claude Opus 4.5 or above, and paste this prompt. The agent will handle browser navigation, credentials, and configuration automatically.

```
I have cloned the AI New-Employee Onboarding Agent project and I need you to set it
up completely so I can run it. Here is what needs to happen:

1. Install Python dependencies from requirements.txt inside a virtual environment.

2. Help me create a .env file by walking me through each API key:
   - OpenAI API key from platform.openai.com. Billing must be enabled.
   - Google Cloud: create a project, enable the Google Sheets API and Gmail API,
     create a service account, download the JSON key as service_account.json,
     create an OAuth 2.0 Desktop Client ID and download it as credentials.json.
   - Zoom: create a Server-to-Server OAuth app at marketplace.zoom.us, activate it,
     add the meeting:write:admin scope, and get the Account ID, Client ID, and
     Client Secret.
   - Supabase: create a free project at supabase.com and get the PostgreSQL
     connection string from Project Settings > Database.

3. Create the Google Sheet with columns A through J: Employee Name, Employee Email,
   Role, Department, Start Date, Manager, Location, Employment Type, Onboarding
   Status, Processed. Share the sheet with the service account email as Editor.

4. Run db/schema.sql against the Supabase database to create the three tables and
   seed the laptop inventory.

5. Complete the one-time Gmail OAuth flow by running gmail_oauth.py so token.json
   is generated.

6. Run python main.py --demo and confirm the output shows Final Status: Completed,
   a real Zoom meeting link, and a confirmation that the welcome email was sent.

Use the browser wherever possible to navigate websites and fill in credentials. Check
each step before moving on and tell me if anything needs my input.
```

After this runs, you will have a real welcome email in your inbox, a real Zoom meeting link you can join, and all employee and task data persisted in your Supabase database.

---

## What It Does

When an HR manager adds a new hire row to a Google Sheet, the system:

1. Classifies the role using GPT-4o-mini and determines which tools and access the hire needs
2. Generates a tailored 12 to 15 task onboarding checklist specific to that role and department
3. Creates an employee record, assigns an available laptop from the IT inventory database, and writes all tasks to PostgreSQL
4. Creates a real Zoom orientation meeting and returns the join link
5. Composes and sends a personalised HTML welcome email via Gmail
6. Marks all tasks as complete, updates the employee status in the database, and writes the status back to the Google Sheet

The entire workflow runs in approximately 45 seconds and completes without any human interaction after the trigger.

---

## LangGraph Architecture

![LangGraph Architecture](docs/architecture.png)

### Node-by-Node Breakdown

The system is implemented as a directed graph built with LangGraph's `StateGraph`. A single `OnboardingState` TypedDict object is passed between every node. Each node reads what it needs, does its work, and writes its results back to the state before the next node runs.

```
Google Sheet (New Row Trigger)
        |
        v
+----------------------------------------------------------+
|              LangGraph StateGraph Orchestrator            |
|                                                          |
|  [1] role_classifier ----> [2] onboarding_planner        |
|                                   |                      |
|                                   v                      |
|                      [3] resource_provisioning            |
|                                   |                      |
|                     +-------------+----------+           |
|                     v                        v           |
|             [4] scheduling_agent   [5] communication_agent|
|                     |                        |           |
|                     +----------+-------------+           |
|                                v                         |
|                      [6] status_updater                  |
+----------------------------------------------------------+
        |                           |
        v                           v
   Google Sheet                PostgreSQL
   (Status Updated)             (Persisted)
```

| Node | Agent | Responsibility | Services |
|------|-------|----------------|----------|
| 1 | Role Classifier | Reads the employee record and uses GPT-4o-mini to output a structured role type and list of required tools | OpenAI GPT-4o-mini |
| 2 | Onboarding Planner | Sends the role type to GPT-4o-mini to generate a full onboarding task list as structured JSON | OpenAI GPT-4o-mini |
| 3 | Resource Provisioning | Writes the employee to the database, assigns the next available laptop from inventory, and inserts all tasks | PostgreSQL via Supabase |
| 4 | Scheduling Agent | Calls the Zoom API to create a new meeting and stores the join URL in state | Zoom Server-to-Server OAuth |
| 5 | Communication Agent | Uses GPT-4o-mini to write an HTML welcome email personalised to the employee, then sends it via Gmail | OpenAI GPT-4o-mini + Gmail API |
| 6 | Status Updater | Marks each task as complete in the database, updates the employee status to Completed, and writes the result back to the Google Sheet | PostgreSQL + Google Sheets API |

### Shared State Schema

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
    errors: List[str]               # Non-fatal errors accumulate here
```

---

## Full Technology Stack

| Category | Technology | Purpose |
|----------|-----------|---------|
| Agent Orchestration | LangGraph 0.2+ | Compiles the six-node StateGraph DAG and manages state transitions |
| Agent Framework | LangChain | Provides the LLM interface, prompt templates, and output parsers used by each agent |
| LLM Runtime | OpenAI GPT-4o-mini | Powers role classification, task list generation, and welcome email writing |
| AI Development | Antigravity + Claude | Used to build, configure, debug, and deploy the entire project |
| Trigger Source | Google Sheets API v4 | Polls the intake spreadsheet every 30 seconds for unprocessed rows |
| Authentication (Sheets) | Google Service Account | Server-to-server auth for reading and writing the Google Sheet without user interaction |
| Email Delivery | Gmail API (OAuth 2.0) | Sends personalised HTML welcome emails from the HR sender address |
| Meeting Scheduling | Zoom Server-to-Server OAuth | Creates real Zoom meetings programmatically and returns join links |
| Database | PostgreSQL via Supabase | Stores employee records, onboarding task lists, and IT inventory (laptops) |
| Database Driver | psycopg2 | Python adapter for connecting to and querying the PostgreSQL database |
| REST API | FastAPI + Uvicorn | Optional HTTP interface for triggering onboarding and querying status |
| Configuration | python-dotenv | Loads environment variables from .env into a typed Settings dataclass |
| HTTP Client | httpx | Used internally by LangChain and the Zoom tool for async API calls |
| Language | Python 3.11+ | Core runtime |

---

## Project Structure

```
ai-onboarding-agent/
|-- main.py                    # CLI entry point: demo / poll / once
|-- api.py                     # FastAPI REST service (optional)
|-- workflow.py                # LangGraph StateGraph construction and compilation
|-- state.py                   # Shared OnboardingState TypedDict schema
|-- config.py                  # Environment config loader with typed Settings class
|-- requirements.txt           # All Python dependencies
|-- .env.example               # Environment variable template with descriptions
|-- docs/
|   `-- architecture.png       # LangGraph architecture diagram
|
|-- agents/                    # One file per LangGraph node
|   |-- role_classifier.py     # Node 1: GPT-4o-mini role and resource classification
|   |-- onboarding_planner.py  # Node 2: GPT-4o-mini task list generation
|   |-- resource_provisioning.py # Node 3: employee record + laptop assignment
|   |-- scheduling_agent.py    # Node 4: Zoom meeting creation
|   |-- communication_agent.py # Node 5: GPT-4o-mini email writing + Gmail send
|   `-- status_updater.py      # Node 6: DB + Sheet status finalisation
|
|-- tools/                     # Thin wrappers around external service APIs
|   |-- google_sheets.py       # Google Sheets API v4: read rows and update status
|   |-- gmail.py               # Gmail API OAuth 2.0: send emails
|   `-- zoom.py                # Zoom Server-to-Server OAuth: create meetings
|
`-- db/                        # Database layer
    |-- schema.sql             # PostgreSQL DDL and 10 laptop seed records
    `-- database.py            # Connection pool and CRUD helpers
```

---

## Quick Start (Manual)

### Prerequisites

- Python 3.11 or higher
- A Supabase account (free tier works) or any PostgreSQL instance
- An OpenAI account with billing enabled
- A Google Cloud project with the Sheets API and Gmail API enabled
- A Zoom Marketplace account for creating a Server-to-Server OAuth app

### 1. Clone and Install

```bash
git clone https://github.com/Safdar-Nizam/Agentic-Onboarding-System.git
cd Agentic-Onboarding-System
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and fill in your credentials
```

Required variables:

```env
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o-mini

GOOGLE_SHEETS_SPREADSHEET_ID=your-sheet-id
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json

GMAIL_SENDER_EMAIL=you@gmail.com
GMAIL_CREDENTIALS_FILE=credentials.json

ZOOM_ACCOUNT_ID=...
ZOOM_CLIENT_ID=...
ZOOM_CLIENT_SECRET=...

DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 3. Set Up the Database

Run the schema against your Supabase project (paste into the SQL editor) or locally:

```bash
psql $DATABASE_URL -f db/schema.sql
```

This creates three tables (`employees`, `onboarding_tasks`, `it_inventory`) and inserts 10 laptop records.

### 4. Set Up Google APIs

**Service Account for Google Sheets:**

1. Open the Google Cloud Console and go to IAM and Admin, then Service Accounts
2. Create a new service account, go to the Keys tab, and add a JSON key
3. Download the file and rename it to `service_account.json`, then place it in the project root
4. Open your Google Sheet and share it with the service account email address as an Editor

**OAuth 2.0 for Gmail:**

1. In APIs and Services, go to Credentials and create an OAuth 2.0 Client ID of type Desktop App
2. Download the JSON and rename it to `credentials.json`, then place it in the project root
3. In the OAuth Consent Screen under Audience, add your Gmail address as a test user
4. Run `python gmail_oauth.py` once to complete the browser sign-in and generate `token.json`

**Google Sheet column format (A through J):**

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| Employee Name | Employee Email | Role | Department | Start Date | Manager | Location | Employment Type | Onboarding Status | Processed |

### 5. Set Up Zoom

1. Go to the Zoom App Marketplace and create a Server-to-Server OAuth app
2. Activate the app and add the scope `meeting:write:admin`
3. Copy the Account ID, Client ID, and Client Secret into your `.env` file

---

## Running the Agent

```bash
# Demo mode: runs with a sample employee, sends real emails and creates real meetings
python main.py --demo

# Live polling: watches your Google Sheet every 30 seconds for new rows
python main.py

# One-shot: process current unprocessed rows and exit
python main.py --once

# REST API
uvicorn api:app --reload --port 8000
```

### Sample Demo Output

```
============================================================
  AI New-Employee Onboarding Agent  v1.0.0
============================================================
  STARTING ONBOARDING: Sarah Chen
  Role: Senior Software Engineer | Dept: Engineering
============================================================
Role Classification Agent  ->  Engineering | Tools: GitHub, Jira, AWS...
Onboarding Plan Agent      ->  12 tasks generated
Resource Provisioning      ->  EMP-7D234C63 | LPT-001 assigned
Scheduling Agent           ->  Zoom meeting created: https://zoom.us/j/...
Communication Agent        ->  Welcome email sent (message id: 19cd5...)
Status Updater             ->  Database -> Completed
============================================================
  ONBOARDING SUMMARY: Sarah Chen
  Employee ID  : EMP-7D234C63
  Laptop       : MacBook Pro 16" M3 (LPT-001)
  Meeting Link : https://us05web.zoom.us/j/84447220010
  Email Sent   : Yes
  Final Status : Completed
============================================================
Demo complete. Finished in ~45 seconds.
```

---

## REST API Reference

Start with `uvicorn api:app --reload --port 8000`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check and version |
| POST | `/onboard` | Trigger onboarding for one employee |
| GET | `/status/{employee_id}` | Query status and task list for an employee |
| GET | `/docs` | Interactive Swagger UI |

Example:

```bash
curl -X POST http://localhost:8000/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane.doe@company.com",
    "role": "Product Manager",
    "department": "Product",
    "start_date": "2026-04-01",
    "manager": "Alex Smith",
    "location": "Remote",
    "employment_type": "Full-time"
  }'
```

---

## Troubleshooting

| Error | Resolution |
|-------|-----------|
| `insufficient_quota` from OpenAI | Add a payment method and credits at platform.openai.com/billing |
| `invalid_client` from Zoom | Double-check the Client Secret character by character, particularly capital I versus lowercase l |
| `credentials.json not found` | Run `python gmail_oauth.py` to complete the one-time OAuth browser consent |
| `Could not deserialize key data` | Re-download `service_account.json` from GCP Console under IAM and Admin, Service Accounts, Keys |
| Google Sheet returns permission denied | Share the sheet with the service account email address and grant Editor access |
| `access_denied` during Gmail OAuth | Add your Gmail address as a Test User in GCP OAuth Consent Screen under Audience |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "Add some feature"`
4. Push to the branch: `git push origin feature/my-feature`
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Further Reading

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Google Sheets API Guide](https://developers.google.com/sheets/api)
- [Zoom Server-to-Server OAuth](https://developers.zoom.us/docs/internal-apps/)
- [DOCUMENTATION.md](DOCUMENTATION.md) for a deep-dive into agent design and state schema
