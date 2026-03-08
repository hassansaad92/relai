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

The app requires three environment variables. Add them to your shell config or a `.env` file:

**Supabase credentials** (found in your Supabase project under Settings → API):

```bash
export SUPABASE_RELAI_URL="https://your-project-id.supabase.co"
export SUPABASE_RELAI_SECRET_KEY="your-supabase-service-role-key"
```

**Anthropic API key** (for the AI chatbot):

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

To make these permanent, add the exports to `~/.zshrc` (macOS default) or `~/.bashrc`:

```bash
echo 'export SUPABASE_RELAI_URL="https://your-project-id.supabase.co"' >> ~/.zshrc
echo 'export SUPABASE_RELAI_SECRET_KEY="your-supabase-service-role-key"' >> ~/.zshrc
echo 'export ANTHROPIC_API_KEY="sk-ant-api03-..."' >> ~/.zshrc
source ~/.zshrc
```

Verify they are set:

```bash
echo $SUPABASE_RELAI_URL
echo $SUPABASE_RELAI_SECRET_KEY
echo $ANTHROPIC_API_KEY
```

> **Getting an Anthropic API key:**
> 1. Go to https://console.anthropic.com
> 2. Sign up or log in
> 3. Navigate to **Settings** → **API Keys** → **Create Key**
> 4. Copy the key (starts with `sk-ant-api03-...`)

> **Security:** Never commit API keys to version control.

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

## License

_(License information to be added)_
