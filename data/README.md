# Data Directory

## History

This project originally used CSV files as its data store:

| File | Description |
|---|---|
| `personnel.csv` | Personnel with skills, availability status, and available date |
| `projects.csv` | Projects with required skills, dates, duration, and status |
| `skills.csv` | Master list of skills |
| `assignments.csv` | Personnel-to-project assignments with sequences and date ranges |

The CSVs used simple integer IDs. We migrated to **Supabase** (Postgres) with UUID primary keys and SCD2 history tables for auditing. The CSVs are kept here as a reference.

The migration was performed via `repopulate_supabase_data.py` (in this directory), which:
1. Inserted projects from CSV, capturing old integer ID → new UUID mappings
2. Fetched personnel already in Supabase, mapping them by name
3. Inserted assignments using the resolved UUIDs

---

## Scripts

| Script | What it does |
|---|---|
| `clear_assignments.py` | Deletes all rows from the `assignments` table only. Everything else (personnel, projects, scenarios, skills, history) is untouched. Useful for testing AI scheduling from scratch. |
| `clear_all_data.py` | Deletes all rows from **every** table (including history tables) in FK-safe order. Schema (tables, triggers, functions) remains intact. Use this to start with empty tables without rebuilding the schema. |
| `drop_all_tables.sql` | Drops all tables **and** their dependent triggers/functions. Run in the Supabase SQL Editor to get a clean slate before re-running `schema.sql`. |
| `schema.sql` | Full Supabase schema (tables, triggers, SCD2 history functions). Run in the SQL Editor to set up or rebuild a project. |
| `repopulate_supabase_data.py` | Re-seeds all data from CSV files into Supabase. Accepts `--seed small` (default) or `--seed large` (~100 crew, ~200 projects — run `generate_large.py` first). |

---

## Setting Up a New Supabase Project

The full schema (tables, triggers, SCD2 history) is in `data/schema.sql`. Run it in the Supabase SQL Editor in one shot.

Table creation order (due to foreign key dependencies):
1. `personnel`
2. `projects`
3. `skills`
4. `scenarios` ← must exist before assignments
5. `assignments`

After running the schema, seed data from CSVs:

```bash
python data/repopulate_supabase_data.py --seed small   # default – original CSV dataset
python data/repopulate_supabase_data.py --seed large   # ~100 crew, ~200 projects
```
