# Scheduling Assistant

An AI-powered crew scheduling system for coordinating elevator installation teams across multiple projects.

## Overview

This application helps coordinate the assignment of mechanics and work crews to projects based on their skills and availability. The system maintains a persistent database of mechanics, projects, and assignments, and uses an AI chatbot to answer scheduling questions in plain language.

## Key Features

- **Gantt chart overview**: Visual timeline of all mechanic assignments across projects
- **AI scheduling assistant**: Ask questions like "Who is available next week?" or "What is John's next project?" and get answers from live data
- **Mechanic management**: Track skills, availability status, and upcoming availability dates
- **Project management**: Track required skills, elevator counts, start dates, and durations
- **Assignment tracking**: Confirmed mechanic-to-project assignments with sequence and date ranges

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **AI**: Anthropic Claude API
- **Frontend**: Vanilla JS + Plotly (Gantt chart)

---

## Getting Started

### Prerequisites

- Python 3.8+
- A [Supabase](https://supabase.com) project with the schema below
- An [Anthropic API key](https://console.anthropic.com) for the AI chatbot

### 1. Clone the repo

```bash
git clone <repository-url>
cd relai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

The app requires the following environment variables. Add them to your shell config or a `.env` file:

**Supabase database credentials** (found in your Supabase project under Settings → Database):

```bash
export SUPABASE_RELAI_DB_HOST="db.your-project-id.supabase.co"
export SUPABASE_RELAI_DB_PASSWORD="your-postgres-password"
```

**Anthropic API key** (for the AI chatbot):

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

To make these permanent, add the exports to `~/.zshrc` (macOS default) or `~/.bashrc`:

```bash
echo 'export SUPABASE_RELAI_DB_HOST="db.your-project-id.supabase.co"' >> ~/.zshrc
echo 'export SUPABASE_RELAI_DB_PASSWORD="your-postgres-password"' >> ~/.zshrc
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-..."' >> ~/.zshrc
source ~/.zshrc
```

Verify they are set:

```bash
echo $SUPABASE_RELAI_DB_HOST
echo $SUPABASE_RELAI_DB_PASSWORD
echo $ANTHROPIC_API_KEY
```

> **Getting an Anthropic API key:**
> 1. Go to https://console.anthropic.com
> 2. Sign up or log in
> 3. Navigate to **Settings** → **API Keys** → **Create Key**
> 4. Copy the key (starts with `sk-ant-api03-...`)

> **Security:** Never commit API keys to version control.

### Data reset script

`data/reset_supabase_data.py` reseeds the database from CSV files using the Supabase Python client. It requires two additional env vars — the project URL (same host as `SUPABASE_RELAI_DB_HOST` but replacing `db.` with `https://`) and a service role key:

```bash
export SUPABASE_RELAI_URL="https://your-project-id.supabase.co"
export SUPABASE_RELAI_SECRET_KEY="your-supabase-service-role-key"
```

These are only needed when running the reset script, not for the main app.

### 4. Run the app

```bash
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

---

## Database Schema (Supabase)

Create these tables in your Supabase project:

**mechanics**
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, default `gen_random_uuid()` |
| `name` | Text | |
| `skills` | Text | Comma-separated skill tags |
| `availability_status` | Text | e.g. `available`, `assigned` |
| `available_date` | Date | When they next become free |

**projects**
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, default `gen_random_uuid()` |
| `name` | Text | |
| `required_skills` | Text | Comma-separated skill tags |
| `num_elevators` | Integer | |
| `start_date` | Date | |
| `duration_weeks` | Integer | |
| `status` | Text | e.g. `upcoming`, `in_progress`, `completed` |

**assignments**
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, default `gen_random_uuid()` |
| `mechanic_id` | UUID | Foreign key → mechanics |
| `project_id` | UUID | Foreign key → projects |
| `sequence` | Integer | Order of assignment for this mechanic |
| `start_date` | Date | |
| `end_date` | Date | |

**skills**
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, default `gen_random_uuid()` |
| `skill` | Text | Skill name |

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/mechanics` | List all mechanics |
| `POST` | `/api/mechanics` | Add a mechanic |
| `GET` | `/api/projects` | List all projects |
| `POST` | `/api/projects` | Add a project |
| `GET` | `/api/assignments` | List all assignments |
| `GET` | `/api/skills` | List all skills |
| `POST` | `/api/skills` | Add a skill |
| `POST` | `/api/chat` | Send a message to the AI assistant |

---

## Decision Log

Chronological record of major technical decisions and what shipped in each PR.

---

### PR #1 — Initial app scaffolding
**Branch:** `feature/add-data-directory-csvs`

- Chose FastAPI + Vanilla JS (no frontend framework) to keep the stack minimal and fast to iterate on
- Added CSV files in `data/` as the initial data source
- Added sidebar navigation and a basic skills management UI

---

### PR #2 — API refactor
**Branch:** `feature/refactor-api-endpoints`

- Refactored all API routes to clean `/api/<resource>` URL patterns
- Separated route logic from `main.py` into `api.py` using an `APIRouter`

---

### PR #4 — Gantt chart overview
**Branch:** `feature/gantt-2`

- Added Plotly.js Gantt chart as the default home/overview page
- Added a dedicated `/api/assignments` endpoint to serve assignment data to the chart
- Removed Asana GID references (switched to internal IDs)

---

### PR #5 — Supabase integration
**Branch:** `feature/data-and-frontend-2`

- Replaced CSV-based data with a live Supabase (PostgreSQL) database
- Used the Supabase Python client (`supabase-py`) for all DB operations
- Added alphabetical sorting to personnel/project list views
- Added initial data migration script

---

### PR #6 — AI chatbot
**Branch:** `feature/chatbot-1`

- Added an AI chatbot (Anthropic Claude API) with live assignment data injected as context
- Chatbot replaces a naive static-response approach that was giving incorrect scheduling answers

---

### PR #7 — Rename mechanics → personnel
**Branch:** `feature/rename-mechanics-to-personnel`

- Renamed "mechanics" to "personnel" throughout the app (DB table, API, UI) to be more generic
- Compacted UI spacing for better information density

---

### PR #8 — Scenario versioning
**Branch:** `feature/scenario-versioning`

- Added a `scenarios` table with a master/draft workflow
- All assignments now belong to a scenario; the master scenario represents the live schedule
- Drafts can be created from master, edited independently, and promoted back to master

---

### PR #9 — Manual assignment management
**Branch:** `feature/manual-assignments-2`

- Added a Schedule tab for creating, editing, and deleting assignments manually
- Assignments are scoped to the active scenario

---

### PR #10 — Data reset script
**Branch:** `feature/reseed-migration-script`

- Renamed `migrate_to_supabase.py` → `reset_supabase_data.py` to reflect its actual purpose (reset + reseed, not one-time migration)
- Script deletes all rows and re-inserts from CSVs using the Supabase service-role client

---

### PR #11 — Migrate DB layer to psycopg2
**Branch:** `data/psycopg2-migration`

- Replaced the Supabase Python client (`supabase-py`) with `psycopg2` + a `ThreadedConnectionPool`
- **Why:** The Supabase client requires the service-role secret key, which has admin-level access. Direct PostgreSQL credentials (`DB_HOST` + `DB_PASSWORD`) are sufficient for the app and follow the principle of least privilege
- Env vars changed: `SUPABASE_RELAI_URL` + `SUPABASE_RELAI_SECRET_KEY` → `SUPABASE_RELAI_DB_HOST` + `SUPABASE_RELAI_DB_PASSWORD`
- Pool is initialized/closed via FastAPI `lifespan` context manager
- The data reset script (`reset_supabase_data.py`) still uses the Supabase client and still requires the service-role key — those env vars now only apply to that script
- Moved raw SQL queries to `queries.sql` for reference
- Added `.claude/skills/supabase-connection/` skill documenting the connection details

---

## License

_(License information to be added)_
