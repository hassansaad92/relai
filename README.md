# Scheduling Assistant

An AI-powered crew scheduling system for coordinating elevator installation teams across multiple projects.

## Overview

This application helps coordinate the assignment of mechanics and work crews to projects based on their skills and availability. The system maintains a persistent database of mechanics, projects, and assignments, and uses an AI chatbot to answer scheduling questions in plain language.

## Key Features

- **Gantt chart overview**: Visual timeline of all mechanic assignments across projects
- **AI scheduling assistant**: Ask questions like "Who is available next week?" or "What is John's next project?" and get answers from live data
- **Personnel management**: Track skills; availability is automatically derived from assignments
- **Project management**: Track required skills, committed/actual dates, fractional durations, and procurement dates
- **Assignment tracking**: Personnel-to-project assignments with sequence, date ranges, assignment types, and daily allocation (half/full day)

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
| `committed_start_date` | Date | Optional committed start date |
| `committed_end_date` | Date | Optional committed completion date |
| `duration_days` | Numeric(5,1) | Supports fractional days (0.5, 1.0, 1.5, etc.) |
| `procurement_date` | Date | Optional procurement/material date |
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
| `allocated_days` | Numeric(5,1) | Daily allocation (0.5 = half day, 1.0 = full day) |
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
| `POST` | `/api/projects` | Add a project (`committed_end_date` computed server-side when start date provided) |
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
- **Split project dates**: renamed `start_date` → `committed_start_date`, added `committed_end_date` (computed server-side). Both are optional — service work may not have committed dates. Actual dates (`actual_start_date`, `actual_end_date`) are computed from assignment JOINs
- **Added `assignment_type`**: supports 3 scheduling scenarios — `full` (project start to end), `cascading` (personnel's next available date + duration), and `partial` (custom dates). CHECK constraint enforces valid values
- **Extracted SQL into `queries/` directory**: 6 `.sql` files with proper JOINs replace inline SQL and frontend-side data joining. Loaded via `_load_sql()` with `@lru_cache`
- **Eliminated frontend availability management**: `scheduleAssign()` and `scheduleRemove()` no longer PATCH personnel — the source of truth is assignments, and the UI reads derived state from the server

---

### Sidebar hover-expand, assignment end-date cascade, and schedule/project tab separation
**Branch:** `feature/assignment-end-date-cascade`

- **Sidebar hover-expand**: Replaced toggle-button collapse with CSS hover. Sidebar starts at 56px (icons only) and expands to 250px on hover. Uses `opacity` transitions on labels so icons never shift position. Removed `toggleSidebar()`, all `.sidebar.collapsed` rules, and `body.sidebar-collapsed` classes
- **Schedule tab — assignment-level editing only**: Removed committed start/end/duration editing from the schedule panel. Each assigned person now has an inline end-date editor that calls a cascade endpoint. Cascade pushes or pulls subsequent assignments for the same person, preserving each assignment's duration
- **Projects tab — project-level editing only**: Committed start date and duration are edited in the project modal. Added a Committed End Date field with bidirectional sync (changing duration updates end date and vice versa)
- **Bidirectional cascade**: The `cascade_assignment_end_date` DB function now handles both directions — pushing assignments forward when end dates extend (overlap detection) and pulling them back when end dates shrink (delta-based shift with floor at previous assignment's end)
- **API**: Added `committed_end_date` to `ProjectUpdate` model. PATCH handler calculates `duration_days` when only end date is provided. Cascade endpoint auto-extends project `committed_end_date` if any shifted assignment exceeds it

---

### PR #34 — Fix project name lookup bug, add prompt logging, enable RLS
**Branch:** `feature/project-lookup-fix-prompt-logging`

- **Project name lookup fix**: After the AI creates a schedule, it could no longer reference projects by name because scheduled projects disappeared from the UNSCHEDULED list and were only buried inside personnel assignment details. Added an "ALL PROJECTS (reference)" section to the AI context that lists every awarded project with its ID and name, giving the AI a reliable lookup table regardless of scheduling status
- **Prompt logging**: Added a `chat_logs` table to capture every user prompt sent to the AI chatbot, along with the active scenario ID and whether the user was in tweak mode. Logged fire-and-forget so failures never break chat. Purpose: understand how users interact with the AI for future improvements
- **Enabled Row Level Security (RLS) on all tables**: Supabase warns when RLS is disabled because its REST API (`postgrest`) is publicly accessible — anyone with the project URL and `anon` key can query tables directly, bypassing the backend. Enabling RLS closes this vector. We added permissive allow-all policies (`USING (true) WITH CHECK (true)`) because our app doesn't use the Supabase client SDK — it connects via `psycopg2` using the `postgres` role, which **bypasses RLS entirely** (RLS only applies to non-superuser roles like `anon` and `authenticated`). So our backend access is unaffected, but unauthenticated REST API access is now blocked by default

---

## Roadmap

### Phase 1: Service Work Pivot (Current)
- Fractional-day durations (0.5, 1.0, 1.5, etc.)
- Half-day assignments with capacity-based conflict detection
- Procurement date tracking per project
- Dual mechanic assignments within a single day

### Phase 1.5: Configurable Risk Badges & Settings Tab
- Add a Settings tab for user-configurable risk thresholds
- **Mobilization Risk**: user defines a threshold (e.g., 5 days) — projects without materials or assignments within that window of their committed start date are flagged
- **Delay Risk**: user defines criteria for flagging projects at risk of schedule delay
- Risk badges displayed on schedule project cards based on these definitions
- Thresholds persisted per user/scenario

### Phase 2: Authentication & User Accounts
- User sign-in (OAuth or email/password)
- Role-based access control (admin, scheduler, viewer)
- Session management and API auth

### Phase 3: Multi-Tenancy
- Per-company databases or isolated table sets
- Company onboarding and provisioning
- Data isolation between tenants

### Phase 4: GPS-Based Proximity Optimization
- Geocoding project addresses
- Proximity-aware scheduling suggestions
- Travel time estimation between job sites

### Phase 5: Contract Management
- Contract document storage via AWS S3
- Link contracts to projects
- Document versioning and access control

---

## License

_(License information to be added)_
