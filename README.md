# Scheduling Assistant

An AI-powered crew scheduling system that optimizes work crew assignments for construction and maintenance projects.

## Overview

This application helps coordinate and optimize the assignment of mechanics and work crews to projects based on their skills, equipment expertise, and project requirements. Rather than generating schedules on-demand, the system maintains a persistent database of current assignments and intelligently determines the optimal next job for each crew as they complete their work.

## How It Works

The scheduling assistant maintains state about:
- **Mechanics/Crews**: Individual workers or teams, including their skillsets, equipment proficiencies, and current assignments
- **Projects**: Work to be done, including building types, start dates, durations, and requirements
- **Current Assignments**: Active crew-to-project mappings with projected completion dates

When optimization is triggered, the system uses Claude AI to analyze constraints and available resources, then determines the best next assignment for crews approaching completion of their current work.

## Key Features

- **Constraint-based optimization**: Matches crew capabilities with project requirements
- **Skill and equipment tracking**: Ensures the right expertise is assigned to each job
- **Projected timeline management**: Tracks when crews will be available for reassignment
- **AI-powered decision making**: Leverages Claude API to make intelligent scheduling decisions
- **Persistent state**: Database-driven approach for reliable tracking across sessions

## Use Cases

- Construction project crew scheduling
- Maintenance team coordination
- Multi-site service crew optimization
- Any scenario requiring skilled worker allocation across time-bound projects

## Technical Implementation

### Stack

- **Backend**: FastAPI (Python)
- **Database**: Supabase (PostgreSQL)
- **AI**: Anthropic Claude API

### API Structure

The FastAPI application provides endpoints for:
- Managing mechanics and crews (CRUD operations)
- Managing projects (CRUD operations)
- Triggering optimization runs
- Viewing current and upcoming assignments
- Querying crew availability and project status

### Database Schema (Supabase)

**mechanics**
- `id`: UUID (primary key)
- `name`: Text
- `skills`: JSONB (array of skill tags)
- `equipment_expertise`: JSONB (array of equipment types)
- `availability_status`: Text (available, assigned, unavailable)
- `created_at`: Timestamp

**projects**
- `id`: UUID (primary key)
- `name`: Text
- `building_type`: Text
- `start_date`: Date
- `duration_days`: Integer
- `requirements`: JSONB (required skills, equipment, crew size)
- `status`: Text (pending, in_progress, completed)
- `created_at`: Timestamp

**assignments**
- `id`: UUID (primary key)
- `mechanic_id`: UUID (foreign key → mechanics)
- `project_id`: UUID (foreign key → projects)
- `assigned_at`: Timestamp
- `projected_completion`: Date
- `actual_completion`: Date (nullable)
- `status`: Text (active, completed)

**optimization_runs**
- `id`: UUID (primary key)
- `run_at`: Timestamp
- `assignments_created`: Integer
- `parameters`: JSONB (snapshot of constraints/inputs)
- `result_summary`: Text

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Anthropic API key (for AI-powered scheduling optimization)

### Getting an Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in to your account
3. Navigate to **Settings** → **API Keys**
4. Click **Create Key**
5. Copy your API key (starts with `sk-ant-api03-...`)

### Setting Up Your API Key

Add your API key to your shell configuration file:

**For macOS/Linux (zsh):**
```bash
echo "export ANTHROPIC_API_KEY='your-api-key-here'" >> ~/.zshrc
source ~/.zshrc
```

**For macOS/Linux (bash):**
```bash
echo "export ANTHROPIC_API_KEY='your-api-key-here'" >> ~/.bashrc
source ~/.bashrc
```

**To verify it's set:**
```bash
echo $ANTHROPIC_API_KEY
```

**⚠️ Security Note:** Never commit your API key to version control or share it publicly.

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd scheduling_assistant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

1. Start the FastAPI server (choose one method):

   **Option A - Simple:**
   ```bash
   python main.py
   ```

   **Option B - Using uvicorn directly:**
   ```bash
   uvicorn main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

The application will be running with:
- **Frontend UI**: http://localhost:8000
- **API Endpoints**:
  - `GET /mechanics` - Retrieve all mechanics
  - `GET /projects` - Retrieve all projects

### Development

The server runs with `--reload` flag, which means it will automatically restart when you make changes to the code.

## License

_(License information to be added)_
