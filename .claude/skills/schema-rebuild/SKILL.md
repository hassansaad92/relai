# Schema Rebuild

**MANDATORY**: When making ANY changes to `data/schema.sql` (adding/removing/altering tables, triggers, or functions), you MUST also review and update the related data scripts to stay in sync.

## Rebuild Workflow

The user's full rebuild flow is:

1. `python data/drop_all_tables.py` — drops all tables, triggers, and functions
2. Run `data/schema.sql` in the Supabase SQL Editor — recreates everything
3. `python data/repopulate_supabase_data.py --seed small|large` — re-seeds data from CSVs

## What to Review on Schema Changes

When `data/schema.sql` is modified, check and update each of these files:

| File | What to check |
|---|---|
| `data/drop_all_tables.py` | Does the `DROP_SQL` block list all current tables and functions? Add any new ones, remove any deleted ones. |
| `data/clear_all_data.py` | Does the `TABLES` list include all current tables in the correct FK-safe deletion order? |
| `data/clear_assignments.py` | Only if the `assignments` table itself changed (renamed, removed, PK changed). |
| `data/repopulate_supabase_data.py` | If new tables were added or columns changed, update the CSV-to-Supabase insertion logic. |
| `data/README.md` | Update the table creation order and script descriptions if the schema changed significantly. |

## Checklist

Before committing schema changes, confirm:

- [ ] `drop_all_tables.py` drops every table and function in the new schema
- [ ] `clear_all_data.py` deletes from every table in FK-safe order
- [ ] `repopulate_supabase_data.py` inserts into all required tables with correct columns
- [ ] `data/README.md` reflects the current table creation order
- [ ] The full rebuild flow works: drop → schema.sql → repopulate
