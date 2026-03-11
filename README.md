# Scheduling Assistant

An AI-powered crew scheduling system for coordinating elevator installation teams across multiple projects.

## Overview

This application helps coordinate the assignment of mechanics and work crews to projects based on their skills and availability. The system maintains a persistent database of mechanics, projects, and assignments, and uses an AI chatbot to answer scheduling questions in plain language.

## Key Features

- **Gantt chart overview**: Visual timeline of all mechanic assignments across projects
- **AI scheduling assistant**: Ask questions like "Who is available next week?" or "What is John's next project?" and get answers from live data
- **Personnel management**: Track skills; availability is automatically derived from assignments
- **Project management**: Track required skills, elevator counts, requested/actual dates, and durations
- **Assignment tracking**: Confirmed personnel-to-project assignments with sequence, date ranges, and assignment types (full/cascading/partial)

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

`data/repopulate_supabase_data.py` reseeds the database from CSV files using the Supabase Python client. It requires two additional env vars — the project URL (same host as `SUPABASE_RELAI_DB_HOST` but replacing `db.` with `https://`) and a service role key:

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

Run `data/schema.sql` in the Supabase SQL Editor to create all tables, triggers, and history tables.

**personnel** — pure dimension table; availability is derived from assignments via queries
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, default `gen_random_uuid()` |
| `name` | Text | |
| `skills` | Text | Comma-separated skill tags |
| `created_at` | Timestamptz | Auto-set |
| `updated_at` | Timestamptz | Auto-updated via trigger |

**projects**
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, default `gen_random_uuid()` |
| `name` | Text | |
| `requested_start_date` | Date | When the project is requested to start |
| `requested_end_date` | Date | Computed from `requested_start_date + duration_weeks` |
| `duration_weeks` | Integer | |
| `num_elevators` | Integer | |
| `required_skills` | Text | Comma-separated skill tags |
| `award_status` | Text | `awarded` or `prospect` |
| `created_at` | Timestamptz | Auto-set |
| `updated_at` | Timestamptz | Auto-updated via trigger |

**assignments**
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, default `gen_random_uuid()` |
| `personnel_id` | UUID | Foreign key → personnel |
| `project_id` | UUID | Foreign key → projects |
| `scenario_id` | UUID | Foreign key → scenarios |
| `sequence` | Integer | Order of assignment for this person |
| `start_date` | Date | |
| `end_date` | Date | |
| `assignment_type` | Text | `full`, `cascading`, or `partial` |
| `created_at` | Timestamptz | Auto-set |

**scenarios**
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | Text | |
| `status` | Text | `master` or `draft` |
| `created_from` | UUID | FK → scenarios (branched from) |
| `archived_at` | Timestamptz | null = active |

**skills**
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, default `gen_random_uuid()` |
| `skill` | Text | Unique skill name |

All core tables (personnel, projects, skills) have SCD2 history tables and triggers for audit tracking.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/personnel?scenario_id=` | List personnel with derived availability (enriched via JOIN) |
| `POST` | `/api/personnel` | Add personnel |
| `PATCH` | `/api/personnel/:id` | Update personnel (name, skills) |
| `DELETE` | `/api/personnel/:id` | Delete personnel + their assignments |
| `GET` | `/api/projects?scenario_id=` | List projects with computed schedule_status and actual dates |
| `POST` | `/api/projects` | Add a project (`requested_end_date` computed server-side) |
| `DELETE` | `/api/projects/:id` | Delete project + its assignments |
| `GET` | `/api/assignments?scenario_id=` | Enriched assignments with personnel/project names |
| `GET` | `/api/assignments/overview?scenario_id=` | Gantt chart data with joined names |
| `GET` | `/api/assignments/schedule-projects?scenario_id=` | Schedule tab project list with assignment counts |
| `GET` | `/api/assignments/available-personnel` | Find unassigned personnel for a date range |
| `POST` | `/api/assignments` | Create assignment (with `assignment_type`) |
| `PATCH` | `/api/assignments/:id` | Update assignment |
| `DELETE` | `/api/assignments/:id` | Delete assignment |
| `GET` | `/api/scenarios` | List active scenarios |
| `POST` | `/api/scenarios` | Create draft from master |
| `POST` | `/api/scenarios/:id/promote` | Promote draft to master |
| `DELETE` | `/api/scenarios/:id` | Archive scenario |
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

- Renamed `migrate_to_supabase.py` → `repopulate_supabase_data.py` to reflect its actual purpose (reset + reseed, not one-time migration)
- Script deletes all rows and re-inserts from CSVs using the Supabase service-role client

---

### PR #11 — Migrate DB layer to psycopg2
**Branch:** `data/psycopg2-migration`

- Replaced the Supabase Python client (`supabase-py`) with `psycopg2` + a `ThreadedConnectionPool`
- **Why:** The Supabase client requires the service-role secret key, which has admin-level access. Direct PostgreSQL credentials (`DB_HOST` + `DB_PASSWORD`) are sufficient for the app and follow the principle of least privilege
- Env vars changed: `SUPABASE_RELAI_URL` + `SUPABASE_RELAI_SECRET_KEY` → `SUPABASE_RELAI_DB_HOST` + `SUPABASE_RELAI_DB_PASSWORD`
- Pool is initialized/closed via FastAPI `lifespan` context manager
- The data reset script (`repopulate_supabase_data.py`) still uses the Supabase client and still requires the service-role key — those env vars now only apply to that script
- Moved raw SQL queries to `queries.sql` for reference
- Added `.claude/skills/supabase-connection/` skill documenting the connection details

---

### PR #16 — Normalize data model, extract SQL queries, fix assignment logic
**Branch:** `feature/normalize-data-model-extract-sql`

- **Removed redundant columns**: `personnel.availability_status` and `available_date` were manually maintained via frontend PATCH calls, duplicating what assignments already track. Personnel is now a pure dimension table — availability is derived via LEFT JOIN LATERAL in `queries/personnel_list.sql`
- **Removed `projects.schedule_status`**: was manually set at creation time but should be computed from whether assignments exist. Now derived via LEFT JOIN in `queries/projects_list.sql`
- **Split project dates**: renamed `start_date` → `requested_start_date`, added `requested_end_date` (computed server-side). Actual dates (`actual_start_date`, `actual_end_date`) are computed from assignment JOINs, so project cards now show both requested and scheduled date ranges
- **Added `assignment_type`**: supports 3 scheduling scenarios — `full` (project start to end), `cascading` (personnel's next available date + duration), and `partial` (custom dates). CHECK constraint enforces valid values
- **Extracted SQL into `queries/` directory**: 6 `.sql` files with proper JOINs replace inline SQL and frontend-side data joining. Loaded via `_load_sql()` with `@lru_cache`
- **Eliminated frontend availability management**: `scheduleAssign()` and `scheduleRemove()` no longer PATCH personnel — the source of truth is assignments, and the UI reads derived state from the server

---

## License

_(License information to be added)_
