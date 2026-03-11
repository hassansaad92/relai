"""
Repopulate Supabase from CSVs (skills, personnel, projects, scenarios, assignments).
Deletes all existing data first, then reloads from CSV files.

Run from repo root:
    python data/repopulate_supabase_data.py --seed small   # default
    python data/repopulate_supabase_data.py --seed large   # ~100 crew, ~200 projects
                                                            # (run generate_large.py first)
"""
import argparse
import os
import csv
from pathlib import Path
from supabase import create_client, Client

parser = argparse.ArgumentParser()
parser.add_argument(
    "--seed",
    choices=["small", "large"],
    default="small",
    help="Which seed dataset to load (default: small)",
)
args = parser.parse_args()

SUPABASE_URL = os.environ.get("SUPABASE_RELAI_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_RELAI_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_RELAI_URL or SUPABASE_RELAI_SECRET_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_DIR = Path(__file__).parent / "seeds" / args.seed

if not DATA_DIR.exists():
    raise RuntimeError(
        f"Seed directory not found: {DATA_DIR}\n"
        "For the large seed, run: python data/seeds/generate_large.py"
    )

print(f"Using seed: {args.seed} ({DATA_DIR})\n")

NULL_UUID = "00000000-0000-0000-0000-000000000000"


def read_csv(filename):
    with open(DATA_DIR / filename) as f:
        return list(csv.DictReader(f))


def delete_all(table, pk="id"):
    """Delete all rows from a table."""
    result = supabase.table(table).delete().neq(pk, NULL_UUID if pk == "id" else 0).execute()
    print(f"  Cleared {table} ({len(result.data)} rows deleted)")


# ── 1. Delete all data (reverse FK order) ─────────────────────────────────────
print("Clearing existing data...")
# Clear history tables first to avoid SCD2 trigger issues during deletes
for history_table in ("projects_history", "personnel_history", "skills_history"):
    delete_all(history_table, pk="hid")

delete_all("assignments")
delete_all("scenarios")
delete_all("projects")
delete_all("personnel")
delete_all("skills")

print()

# ── 2. Insert skills ───────────────────────────────────────────────────────────
print("Inserting skills...")
skills_csv = read_csv("skills.csv")
inserted_skills = 0

for row in skills_csv:
    response = supabase.table("skills").insert({"skill": row["skill"]}).execute()
    if not response.data:
        print(f"  ERROR inserting skill: {row['skill']}")
    else:
        print(f"  {row['skill']} -> {response.data[0]['id']}")
        inserted_skills += 1

print(f"Inserted {inserted_skills} skills.\n")

# ── 3. Insert personnel ────────────────────────────────────────────────────────
print("Inserting personnel...")
personnel_csv = read_csv("personnel.csv")
old_personnel_id_to_uuid = {}

for row in personnel_csv:
    payload = {
        "name": row["name"],
        "skills": row["skills"],
    }
    response = supabase.table("personnel").insert(payload).execute()
    if not response.data:
        print(f"  ERROR inserting personnel: {row['name']}")
        continue
    new_uuid = response.data[0]["id"]
    old_personnel_id_to_uuid[row["id"]] = new_uuid
    print(f"  {row['name']} -> {new_uuid}")

print(f"Inserted {len(old_personnel_id_to_uuid)} personnel.\n")

# ── 4. Insert projects ─────────────────────────────────────────────────────────
print("Inserting projects...")
projects_csv = read_csv("projects.csv")
old_project_id_to_uuid = {}

for row in projects_csv:
    payload = {
        "name": row["name"],
        "contract_start_date": row["contract_start_date"],
        "contract_end_date": row["contract_end_date"],
        "duration_weeks": int(row["duration_weeks"]),
        "num_elevators": int(row["num_elevators"]),
        "required_skills": row["required_skills"],
        "award_status": row["award_status"],
    }
    response = supabase.table("projects").insert(payload).execute()
    if not response.data:
        print(f"  ERROR inserting project: {row['name']}")
        continue
    new_uuid = response.data[0]["id"]
    old_project_id_to_uuid[row["id"]] = new_uuid
    print(f"  {row['name']} -> {new_uuid}")

print(f"Inserted {len(old_project_id_to_uuid)} projects.\n")

# ── 5. Seed master scenario ────────────────────────────────────────────────────
print("Seeding master scenario...")
from datetime import datetime, timezone

scenario_response = supabase.table("scenarios").insert({
    "name": "Master Schedule",
    "status": "master",
    "promoted_to_master_at": datetime.now(timezone.utc).isoformat(),
}).execute()

if not scenario_response.data:
    raise RuntimeError("ERROR: failed to create master scenario")

master_scenario_id = scenario_response.data[0]["id"]
print(f"  Master Schedule -> {master_scenario_id}\n")

# ── 6. Insert assignments ──────────────────────────────────────────────────────
print("Inserting assignments...")
assignments_csv = read_csv("assignments.csv")
inserted_assignments = 0

for row in assignments_csv:
    personnel_uuid = old_personnel_id_to_uuid.get(row["personnel_id"])
    project_uuid = old_project_id_to_uuid.get(row["project_id"])

    if not personnel_uuid:
        print(f"  SKIP assignment {row['id']}: personnel_id {row['personnel_id']} not resolved")
        continue
    if not project_uuid:
        print(f"  SKIP assignment {row['id']}: project_id {row['project_id']} not resolved")
        continue

    payload = {
        "personnel_id": personnel_uuid,
        "project_id": project_uuid,
        "scenario_id": master_scenario_id,
        "sequence": int(row["sequence"]),
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "assignment_type": row.get("assignment_type", "full"),
    }
    response = supabase.table("assignments").insert(payload).execute()
    if not response.data:
        print(f"  ERROR inserting assignment {row['id']}")
    else:
        print(f"  Assignment {row['id']} -> {response.data[0]['id']}")
        inserted_assignments += 1

print(f"\nInserted {inserted_assignments} assignments.")
print("\nMigration complete.")
