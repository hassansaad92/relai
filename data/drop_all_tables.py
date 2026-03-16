"""
Drop ALL RelAI tables and their dependent objects (triggers, functions)
from Supabase. This gives you a completely clean slate so you can re-run
schema.sql to rebuild everything.

Run from repo root:
    python data/drop_all_tables.py

After running this, rebuild the schema:
    1. Run data/schema.sql in the Supabase SQL Editor
    2. Re-seed data with: python data/repopulate_supabase_data.py
"""
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_RELAI_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_RELAI_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_RELAI_URL or SUPABASE_RELAI_SECRET_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# SQL to drop everything in the correct order.
# CASCADE ensures triggers and FK constraints are removed automatically.
# Functions are dropped explicitly since they aren't removed by CASCADE on tables.
DROP_SQL = """
-- Drop tables (CASCADE removes triggers and FK constraints)
DROP TABLE IF EXISTS assignments_archive CASCADE;
DROP TABLE IF EXISTS assignments        CASCADE;
DROP TABLE IF EXISTS scenarios          CASCADE;
DROP TABLE IF EXISTS projects_history   CASCADE;
DROP TABLE IF EXISTS projects           CASCADE;
DROP TABLE IF EXISTS personnel_history  CASCADE;
DROP TABLE IF EXISTS personnel          CASCADE;
DROP TABLE IF EXISTS skills_history     CASCADE;
DROP TABLE IF EXISTS skills             CASCADE;

-- Drop trigger functions
DROP FUNCTION IF EXISTS update_personnel_modtime()  CASCADE;
DROP FUNCTION IF EXISTS handle_personnel_scd2()     CASCADE;
DROP FUNCTION IF EXISTS update_projects_modtime()   CASCADE;
DROP FUNCTION IF EXISTS handle_projects_scd2()      CASCADE;
DROP FUNCTION IF EXISTS update_skills_modtime()     CASCADE;
DROP FUNCTION IF EXISTS handle_skills_scd2()        CASCADE;
"""

print("Dropping all tables, triggers, and functions...\n")

try:
    supabase.postgrest.rpc("", {}).execute()  # noqa – not used
except Exception:
    pass  # just checking connectivity

# Execute raw SQL via Supabase's rpc or the REST API
# The supabase-py client doesn't expose raw SQL, so we use the management API
try:
    result = supabase.rpc("exec_sql", {"query": DROP_SQL}).execute()
    print("  All tables, triggers, and functions dropped successfully.")
except Exception:
    # If exec_sql RPC doesn't exist, print the SQL for manual execution
    print("  NOTE: The supabase-py client cannot run raw DDL directly.")
    print("  Copy and run the following SQL in the Supabase SQL Editor:\n")
    print(DROP_SQL)
    print("  Alternatively, create an 'exec_sql' database function:")
    print("    CREATE OR REPLACE FUNCTION exec_sql(query TEXT)")
    print("    RETURNS VOID AS $$ BEGIN EXECUTE query; END; $$ LANGUAGE plpgsql;")

print("\nAfter dropping, rebuild with:")
print("  1. Run data/schema.sql in the Supabase SQL Editor")
print("  2. Re-seed data: python data/repopulate_supabase_data.py")
