"""
Delete all rows from every Supabase table, preserving the schema
(tables, triggers, functions all remain intact).

Deletes in FK-safe order: assignments → scenarios → projects → personnel → skills,
then history tables.

Run from repo root:
    python data/clear_all_data.py
"""
from dotenv import load_dotenv
load_dotenv()

import os
from supabase import create_client, Client

_env = os.environ.get("ENV", "dev").lower()
_pfx = "DEV_SUPABASE" if _env == "dev" else "SUPABASE"
SUPABASE_URL = os.environ.get(f"{_pfx}_URL")
SUPABASE_KEY = os.environ.get(f"{_pfx}_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(f"Missing {_pfx}_URL or {_pfx}_SECRET_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

NULL_UUID = "00000000-0000-0000-0000-000000000000"

# Order matters: delete child rows before parent rows (FK constraints).
TABLES = [
    "chat_logs",
    "assignments_archive",
    "assignments",
    "scenarios",
    "projects",
    "personnel",
    "skills",
    # History tables (no FK constraints, but clear them too)
    "projects_history",
    "personnel_history",
    "skills_history",
]

print("Clearing ALL data from all tables...\n")

for table in TABLES:
    try:
        result = supabase.table(table).delete().neq("id", NULL_UUID).execute()
        print(f"  {table}: deleted {len(result.data)} rows")
    except Exception as e:
        # History tables use 'hid' as PK, not 'id'
        try:
            result = supabase.table(table).delete().neq("hid", 0).execute()
            print(f"  {table}: deleted {len(result.data)} rows")
        except Exception as e2:
            print(f"  {table}: ERROR - {e2}")

print("\nDone. All tables are empty. Schema (tables, triggers, functions) is intact.")
