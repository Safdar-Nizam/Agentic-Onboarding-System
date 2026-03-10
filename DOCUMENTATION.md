# 📖 AI New-Employee Onboarding Agent — Technical Documentation

> Complete technical reference for the LangGraph multi-agent onboarding system.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [Workflow Diagram](#3-workflow-diagram)
4. [Agent Specifications](#4-agent-specifications)
5. [Shared State Schema](#5-shared-state-schema)
6. [Tool Integrations](#6-tool-integrations)
7. [Database Design](#7-database-design)
8. [Error Handling & Retry Strategy](#8-error-handling--retry-strategy)
9. [API Reference](#9-api-reference)
10. [Configuration Reference](#10-configuration-reference)
11. [Setup Guides](#11-setup-guides)
12. [Observability & Logging](#12-observability--logging)

---

## 1. System Overview

The AI New-Employee Onboarding Agent is an automated internal operations system that manages the full lifecycle of onboarding a new hire. It uses **LangGraph** to orchestrate multiple specialised AI agents, each responsible for a distinct onboarding task.

### How It Works (End-to-End)

```
   HR adds new         Python poller        LangGraph              External
   hire to Sheet       detects row          workflow runs          services
   ───────────── ────▶ ─────────────── ────▶ ──────────────── ────▶ ────────────
                                             │                     │
                                             ├─ Role Classifier    │ OpenAI
                                             ├─ Plan Generator     │ OpenAI
                                             ├─ IT Provisioning    │ PostgreSQL
                                             ├─ Zoom Scheduler     │ Zoom API
                                             ├─ Email Sender       │ Gmail API
                                             └─ Status Updater     │ Sheets + DB
                                                                   │
   Updated Sheet  ◀──────────────────────────────────────────────── ┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Agent** | A Python function that receives the shared state, performs an action, and returns state updates |
| **StateGraph** | LangGraph's graph structure connecting agents as nodes with directed edges |
| **Shared State** | A TypedDict (`OnboardingState`) that flows through every node |
| **Conditional Edge** | A routing function that determines the next node based on state |
| **Tool** | An external service integration (Google Sheets, Gmail, Zoom, PostgreSQL) |

---

## 2. Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        TRIGGER LAYER                                 │
│                                                                      │
│   ┌──────────────────┐         ┌──────────────────────────────┐     │
│   │   Google Sheet    │         │  FastAPI REST Endpoint       │     │
│   │   (Auto-Poll)     │         │  POST /onboard               │     │
│   └────────┬─────────┘         └──────────────┬───────────────┘     │
│            │                                   │                     │
│            └───────────────┬───────────────────┘                     │
│                            ▼                                         │
├──────────────────────────────────────────────────────────────────────┤
│                     ORCHESTRATION LAYER                               │
│                                                                      │
│   ┌────────────────────────────────────────────────────────────┐     │
│   │                  LangGraph StateGraph                       │     │
│   │                                                            │     │
│   │   START ──▶ Role Classifier ──▶ Onboarding Planner        │     │
│   │                                        │                   │     │
│   │                                        ▼                   │     │
│   │                              Resource Provisioning          │     │
│   │                                        │                   │     │
│   │                              ┌─────────┴──────────┐        │     │
│   │                              │  Conditional Edge   │        │     │
│   │                              └─────────┬──────────┘        │     │
│   │                          ┌─────────────┼──────────────┐    │     │
│   │                          ▼             │              ▼    │     │
│   │                   Scheduling      (on failure)   Status    │     │
│   │                     Agent          ──────────▶  Updater    │     │
│   │                          │                         ▲       │     │
│   │                          ▼                         │       │     │
│   │                   Communication                    │       │     │
│   │                     Agent ─────────────────────────┘       │     │
│   │                                                            │     │
│   └────────────────────────────────────────────────────────────┘     │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                     INTEGRATION LAYER                                │
│                                                                      │
│   ┌───────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│   │  OpenAI   │  │  Gmail   │  │  Zoom    │  │   PostgreSQL     │  │
│   │  (LLM)    │  │  API     │  │  API     │  │   (Supabase)     │  │
│   └───────────┘  └──────────┘  └──────────┘  └──────────────────┘  │
│                                                                      │
├──────────────────────────────────────────────────────────────────────┤
│                      DATA LAYER                                      │
│                                                                      │
│   ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────┐ │
│   │  employees   │  │ onboarding_tasks │  │  laptop_inventory    │ │
│   └──────────────┘  └──────────────────┘  └──────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Workflow Diagram

### Sequential Agent Execution Flow

```
┌─────────────────┐
│      START       │
│  (New Hire Data) │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐     ┌─────────────────────────────────┐
│  Role Classification │────▶│  Uses OpenAI to classify role   │
│       Agent          │     │  Outputs: role_type, resources  │
└─────────┬───────────┘     └─────────────────────────────────┘
          │
          ▼
┌─────────────────────┐     ┌─────────────────────────────────┐
│  Onboarding Plan    │────▶│  Generates tailored checklist   │
│       Agent          │     │  Output: onboarding_plan[]      │
└─────────┬───────────┘     └─────────────────────────────────┘
          │
          ▼
┌─────────────────────┐     ┌─────────────────────────────────┐
│     Resource         │────▶│  Creates employee record in DB  │
│   Provisioning       │     │  Assigns laptop from inventory  │
│      Agent           │     │  Simulates tool access grants   │
└─────────┬───────────┘     └─────────────────────────────────┘
          │
          ├── Critical failure? ──▶ Skip to Status Update
          │
          ▼
┌─────────────────────┐     ┌─────────────────────────────────┐
│    Scheduling        │────▶│  Creates Zoom meeting           │
│       Agent          │     │  Retries up to 3× on failure   │
└─────────┬───────────┘     └─────────────────────────────────┘
          │
          ▼
┌─────────────────────┐     ┌─────────────────────────────────┐
│   Communication      │────▶│  LLM generates welcome email   │
│       Agent          │     │  Sends via Gmail API            │
│                      │     │  Retries up to 3× on failure   │
└─────────┬───────────┘     └─────────────────────────────────┘
          │
          ▼
┌─────────────────────┐     ┌─────────────────────────────────┐
│   Status Update      │────▶│  Updates Google Sheet row       │
│       Agent          │     │  Updates PostgreSQL status      │
│                      │     │  Logs final summary             │
└─────────┬───────────┘     └─────────────────────────────────┘
          │
          ▼
┌─────────────────┐
│       END        │
│  (Onboarding     │
│   Complete)      │
└─────────────────┘
```

### Decision Logic

```
                    Resource Provisioning
                            │
                    ┌───────┴───────┐
                    │  employee_id   │
                    │   assigned?    │
                    └───────┬───────┘
                            │
               ┌────────────┼────────────┐
               │ YES                     │ NO
               ▼                         ▼
        Scheduling Agent          Status Updater
               │                  (with errors)
               ▼
        Communication Agent
               │
               ▼
        Status Updater
        (success)
```

---

## 4. Agent Specifications

### 4.1 Role Classification Agent

| Property | Value |
|----------|-------|
| **File** | `agents/role_classifier.py` |
| **Function** | `classify_role(state)` |
| **LLM** | OpenAI (temperature=0 for determinism) |
| **Input** | employee_name, role, department, employment_type |
| **Output** | role_type, required_resources |

**Categories**: Engineering, Marketing, Operations, Finance, Human Resources, Design, Sales, Legal, Executive

**How it works**: Sends the employee's role and department to the LLM with a structured prompt. The LLM responds with JSON containing the classification and a list of tools/resources the employee will need. Includes a fallback to "Operations" if parsing fails.

---

### 4.2 Onboarding Plan Agent

| Property | Value |
|----------|-------|
| **File** | `agents/onboarding_planner.py` |
| **Function** | `generate_onboarding_plan(state)` |
| **LLM** | OpenAI (temperature=0.3 for slight creativity) |
| **Input** | role_type, department, employment_type, required_resources |
| **Output** | onboarding_plan (list of task strings) |

**Core tasks always included**:
1. Send welcome email
2. Schedule orientation meeting
3. Assign laptop and equipment
4. Provision software access
5. Create employee ID
6. Notify manager
7. Provide documentation
8. Set up check-ins
9. Complete compliance
10. Final review

Additional role-specific tasks are generated by the LLM.

---

### 4.3 Communication Agent

| Property | Value |
|----------|-------|
| **File** | `agents/communication_agent.py` |
| **Function** | `send_communication(state)` |
| **LLM** | OpenAI (temperature=0.7 for creative writing) |
| **API** | Gmail API (OAuth 2.0) |
| **Retries** | 3 attempts, 5s delay between |

**Email includes**: Personalised greeting, role info, start date, orientation link, resource list, HR contact, encouraging closing.

---

### 4.4 Scheduling Agent

| Property | Value |
|----------|-------|
| **File** | `agents/scheduling_agent.py` |
| **Function** | `schedule_orientation(state)` |
| **API** | Zoom Server-to-Server OAuth |
| **Retries** | 3 attempts, 5s delay between |

**Meeting defaults**: 60 minutes, next day at 10 AM UTC, video on for host and participants.

---

### 4.5 Resource Provisioning Agent

| Property | Value |
|----------|-------|
| **File** | `agents/resource_provisioning.py` |
| **Function** | `provision_resources(state)` |
| **Database** | PostgreSQL |

**Steps**:
1. Generate unique employee ID (`EMP-XXXXXXXX`)
2. Insert employee record
3. Assign first available laptop (with row-level locking)
4. Insert all onboarding task records
5. Simulate tool access grants

---

### 4.6 Status Update Agent

| Property | Value |
|----------|-------|
| **File** | `agents/status_updater.py` |
| **Function** | `update_status(state)` |
| **Outputs to** | Google Sheet + PostgreSQL + Console |

**Status values**: Completed, Completed with Issues

---

## 5. Shared State Schema

The `OnboardingState` TypedDict flows through every agent:

```python
{
    # Employee Info (from trigger)
    "employee_name": "Sarah Chen",
    "employee_email": "sarah.chen@example.com",
    "role": "Senior Software Engineer",
    "department": "Engineering",
    "start_date": "2026-03-15",
    "manager": "David Kim",
    "location": "San Francisco",
    "employment_type": "Full-time",

    # Role Classification
    "role_type": "Engineering",
    "required_resources": ["GitHub", "Jira", "AWS Console"],

    # Onboarding Plan
    "onboarding_plan": ["Send welcome email", "Schedule orientation", ...],

    # Resource Provisioning
    "employee_id": "EMP-A1B2C3D4",
    "assigned_laptop": "LPT-003",

    # Scheduling
    "meeting_link": "https://zoom.us/j/123456789",
    "meeting_details": { ... },

    # Communication
    "email_sent": true,
    "welcome_email_body": "<html>...",

    # Progress
    "tasks_completed": ["Role Classification", "Onboarding Plan", ...],
    "status": "Completed",
    "errors": []
}
```

---

## 6. Tool Integrations

### 6.1 Google Sheets API

| Item | Detail |
|------|--------|
| **File** | `tools/google_sheets.py` |
| **Auth** | Service Account (JSON key file) |
| **Scopes** | `spreadsheets` (read + write) |
| **Read** | Polls for unprocessed rows |
| **Write** | Updates status columns (I, J) |

### 6.2 Gmail API

| Item | Detail |
|------|--------|
| **File** | `tools/gmail.py` |
| **Auth** | OAuth 2.0 (Desktop app) |
| **Scopes** | `gmail.send` |
| **Format** | HTML with plain-text fallback |

### 6.3 Zoom API

| Item | Detail |
|------|--------|
| **File** | `tools/zoom.py` |
| **Auth** | Server-to-Server OAuth |
| **Endpoint** | `POST /v2/users/me/meetings` |
| **Type** | Scheduled meeting (type 2) |

---

## 7. Database Design

### Entity-Relationship Diagram

```
┌────────────────────┐       ┌─────────────────────┐
│     employees      │       │  onboarding_tasks    │
├────────────────────┤       ├─────────────────────┤
│ employee_id  (PK)  │◀──┐  │ task_id      (PK)   │
│ name               │   │  │ employee_id  (FK)   │──▶ employees
│ email (UNIQUE)     │   │  │ task_name           │
│ role               │   │  │ task_status          │
│ department         │   │  │ completed_at         │
│ start_date         │   │  │ created_at           │
│ manager            │   │  └─────────────────────┘
│ location           │   │
│ employment_type    │   │  ┌─────────────────────┐
│ status             │   │  │  laptop_inventory    │
│ created_at         │   │  ├─────────────────────┤
│ updated_at         │   │  │ laptop_id    (PK)   │
└────────────────────┘   │  │ model               │
                         │  │ status              │
                         └──│ assigned_to  (FK)   │──▶ employees
                            │ assigned_at          │
                            │ created_at           │
                            └─────────────────────┘
```

### Table Details

**employees** — Central employee record created during provisioning.

| Column | Type | Notes |
|--------|------|-------|
| employee_id | TEXT PK | Format: `EMP-XXXXXXXX` |
| email | TEXT UNIQUE | Prevents duplicate processing |
| status | TEXT | Pending → In Progress → Completed |

**onboarding_tasks** — One row per checklist item per employee.

| Column | Type | Notes |
|--------|------|-------|
| task_id | SERIAL PK | Auto-increment |
| employee_id | TEXT FK | Cascading delete |
| task_status | TEXT | Pending → Completed |

**laptop_inventory** — Pre-seeded with 10 laptops.

| Column | Type | Notes |
|--------|------|-------|
| laptop_id | TEXT PK | Format: `LPT-XXX` |
| status | TEXT | Available → Assigned |
| assigned_to | TEXT FK | NULL until assigned |

---

## 8. Error Handling & Retry Strategy

```
┌──────────────────────────┐
│     Error Occurs          │
└────────────┬─────────────┘
             │
    ┌────────┴────────┐
    │ Retryable?       │
    └────────┬────────┘
             │
     ┌───────┼───────┐
     │ YES           │ NO
     ▼               ▼
  Retry up to    Log error
  3 times        Add to state.errors
  (5s delay)     Continue workflow
     │
     │ All failed?
     ▼
  Log error
  Add to state.errors
  Continue workflow
```

| Agent | Retry? | Max Attempts | On Final Failure |
|-------|--------|-------------|------------------|
| Role Classifier | No | 1 | Falls back to "Operations" |
| Onboarding Planner | No | 1 | Uses default 10-item checklist |
| Communication Agent | **Yes** | 3 | Logs warning, email_sent=False |
| Scheduling Agent | **Yes** | 3 | Logs alert for manual scheduling |
| Resource Provisioning | No | 1 | Logs procurement alert if no laptops |
| Status Updater | No | 1 | Logs error, continues |

---

## 9. API Reference

### Health Check

```http
GET /
```

Response:
```json
{
  "service": "AI Onboarding Agent",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

### Trigger Onboarding

```http
POST /onboard
Content-Type: application/json

{
  "employee_name": "Sarah Chen",
  "employee_email": "sarah.chen@example.com",
  "role": "Senior Software Engineer",
  "department": "Engineering",
  "start_date": "2026-03-15",
  "manager": "David Kim",
  "location": "San Francisco",
  "employment_type": "Full-time"
}
```

Response:
```json
{
  "employee_id": "EMP-A1B2C3D4",
  "employee_name": "Sarah Chen",
  "status": "Completed",
  "tasks_completed": [
    "Role Classification",
    "Onboarding Plan Generation",
    "Resource Provisioning",
    "Orientation Scheduling",
    "Welcome Email",
    "Status Update"
  ],
  "meeting_link": "https://zoom.us/j/123456789",
  "assigned_laptop": "LPT-001",
  "email_sent": true,
  "errors": []
}
```

### Get Status

```http
GET /status/EMP-A1B2C3D4
```

Response:
```json
{
  "employee_id": "EMP-A1B2C3D4",
  "name": "Sarah Chen",
  "email": "sarah.chen@example.com",
  "role": "Senior Software Engineer",
  "department": "Engineering",
  "status": "Completed",
  "tasks": [
    {
      "task_id": 1,
      "task_name": "Send welcome email",
      "task_status": "Completed",
      "completed_at": "2026-03-08T23:00:00Z"
    }
  ]
}
```

---

## 10. Configuration Reference

All settings are loaded from `.env` via `config.py`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ | — | OpenAI API key |
| `OPENAI_MODEL` | ❌ | `gpt-4o-mini` | Model for LLM agents |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | ✅ | — | Google Sheet ID |
| `GOOGLE_SHEETS_RANGE` | ❌ | `Sheet1!A:J` | Range to poll |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | ✅ | `service_account.json` | Path to SA key |
| `GMAIL_SENDER_EMAIL` | ✅ | — | "From" address |
| `GMAIL_CREDENTIALS_FILE` | ✅ | `credentials.json` | OAuth client secrets |
| `GMAIL_TOKEN_FILE` | ❌ | `token.json` | Cached refresh token |
| `ZOOM_ACCOUNT_ID` | ✅ | — | Zoom S2S Account ID |
| `ZOOM_CLIENT_ID` | ✅ | — | Zoom S2S Client ID |
| `ZOOM_CLIENT_SECRET` | ✅ | — | Zoom S2S Client Secret |
| `DB_HOST` | ❌ | `localhost` | PostgreSQL host |
| `DB_PORT` | ❌ | `5432` | PostgreSQL port |
| `DB_NAME` | ❌ | `onboarding_db` | Database name |
| `DB_USER` | ❌ | `postgres` | Database user |
| `DB_PASSWORD` | ✅ | — | Database password |
| `POLL_INTERVAL_SECONDS` | ❌ | `30` | Sheet poll frequency |

---

## 11. Setup Guides

### 11.1 Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable APIs:
   - **Google Sheets API**
   - **Gmail API**
4. **Service Account** (for Sheets):
   - IAM & Admin → Service Accounts → Create
   - Download JSON key → save as `service_account.json`
   - Share the Google Sheet with the SA email
5. **OAuth 2.0** (for Gmail):
   - APIs & Services → Credentials → Create OAuth Client ID
   - Application type: Desktop
   - Download JSON → save as `credentials.json`

### 11.2 Zoom Setup

1. Go to [Zoom Marketplace](https://marketplace.zoom.us/)
2. Develop → Build App → Server-to-Server OAuth
3. Add scopes: `meeting:write:admin`
4. Copy Account ID, Client ID, Client Secret to `.env`

### 11.3 PostgreSQL Setup

**Option A — Local**:
```bash
psql -U postgres -c "CREATE DATABASE onboarding_db;"
psql -U postgres -d onboarding_db -f db/schema.sql
```

**Option B — Supabase**:
1. Create project at [supabase.com](https://supabase.com)
2. Go to SQL Editor → paste contents of `db/schema.sql` → Run
3. Copy connection string to `DATABASE_URL` in `.env`

**Option C — Neon**:
1. Create project at [neon.tech](https://neon.tech)
2. Run schema via their SQL console
3. Copy connection string to `.env`

### 11.4 Google Sheet Template

Create a sheet with this header row (A1–J1):

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| Employee Name | Employee Email | Role | Department | Start Date | Manager | Location | Employment Type | Onboarding Status | Processed |

---

## 12. Observability & Logging

All modules use Python's `logging` module with a consistent format:

```
2026-03-08 22:55:00 │ INFO     │ agents.role_classifier      │ ▶ Role Classification Agent — classifying Sarah Chen
2026-03-08 22:55:02 │ INFO     │ agents.role_classifier      │ ✔ Role classified → Engineering
2026-03-08 22:55:02 │ INFO     │ agents.onboarding_planner   │ ▶ Onboarding Plan Agent — building plan
```

### Log Levels

| Level | Usage |
|-------|-------|
| **DEBUG** | Detailed API payloads, tokens |
| **INFO** | Agent start/end, task completion, normal flow |
| **WARNING** | Retry attempts, empty laptop inventory |
| **ERROR** | API failures, database errors |

### Setting Log Level

```bash
python main.py --log-level DEBUG
```

### What Gets Logged

- ⏱ Agent execution timing
- 🔧 Tool calls (API requests/responses)
- ❌ Errors with full stack traces
- ✅ Workflow start/completion summaries
- 📊 Final onboarding summary table
