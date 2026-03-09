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

The migration was performed via `reset_supabase_data.py` (in this directory), which:
1. Inserted projects from CSV, capturing old integer ID → new UUID mappings
2. Fetched personnel already in Supabase, mapping them by name
3. Inserted assignments using the resolved UUIDs

---

## Setting Up a New Supabase Project

The full schema (tables, triggers, SCD2 history) is in `data/schema.sql`. Run it in the Supabase SQL Editor in one shot.

Table creation order (due to foreign key dependencies):
1. `personnel`
2. `projects`
3. `skills`
4. `scenarios` ← must exist before assignments
5. `assignments`

After running the schema, seed the initial master scenario and re-seed data from CSVs:

```bash
python data/reset_supabase_data.py
```

Note: the script expects personnel and skills to already be in Supabase (insert those manually or extend the script), then handles projects and assignments automatically.
