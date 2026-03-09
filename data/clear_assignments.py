"""
Clear all assignments from the database without touching any other data.
Useful for testing AI scheduling suggestions from scratch.

Run from repo root:
    python data/clear_assignments.py
"""
import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_RELAI_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_RELAI_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_RELAI_URL or SUPABASE_RELAI_SECRET_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

NULL_UUID = "00000000-0000-0000-0000-000000000000"

print("Clearing assignments...")
result = supabase.table("assignments").delete().neq("id", NULL_UUID).execute()
print(f"  Deleted {len(result.data)} assignments.")
print("\nDone. Scenarios, personnel, and projects are untouched.")
