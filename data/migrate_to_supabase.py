"""
Full migration: all CSVs -> Supabase (mechanics, skills, projects, assignments).
Run this from the repo root: python data/migrate_to_supabase.py
"""
import os
import csv
from pathlib import Path
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_RELAI_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_RELAI_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_RELAI_URL or SUPABASE_RELAI_SECRET_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_DIR = Path(__file__).parent


def read_csv(filename):
    with open(DATA_DIR / filename) as f:
        return list(csv.DictReader(f))


# ── 1. Insert skills ──────────────────────────────────────────────────────────
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

# ── 2. Insert mechanics ───────────────────────────────────────────────────────
print("Inserting mechanics...")
mechanics_csv = read_csv("mechanics.csv")
old_mechanic_id_to_uuid = {}

for row in mechanics_csv:
    payload = {
        "name": row["name"],
        "skills": row["skills"],
        "availability_status": row["availability_status"],
        "available_date": row["available_date"],
    }
    response = supabase.table("mechanics").insert(payload).execute()
    if not response.data:
        print(f"  ERROR inserting mechanic: {row['name']}")
        continue
    new_uuid = response.data[0]["id"]
    old_mechanic_id_to_uuid[row["id"]] = new_uuid
    print(f"  {row['name']} -> {new_uuid}")

print(f"Inserted {len(old_mechanic_id_to_uuid)} mechanics.\n")

# ── 3. Insert projects ────────────────────────────────────────────────────────
print("Inserting projects...")
projects_csv = read_csv("projects.csv")
old_project_id_to_uuid = {}

for row in projects_csv:
    payload = {
        "name": row["name"],
        "start_date": row["start_date"],
        "duration_weeks": int(row["duration_weeks"]),
        "num_elevators": int(row["num_elevators"]),
        "required_skills": row["required_skills"],
        "status": row["status"],
    }
    response = supabase.table("projects").insert(payload).execute()
    if not response.data:
        print(f"  ERROR inserting project: {row['name']}")
        continue
    new_uuid = response.data[0]["id"]
    old_project_id_to_uuid[row["id"]] = new_uuid
    print(f"  {row['name']} -> {new_uuid}")

print(f"Inserted {len(old_project_id_to_uuid)} projects.\n")

# ── 4. Insert assignments ─────────────────────────────────────────────────────
print("Inserting assignments...")
assignments_csv = read_csv("assignments.csv")

for row in assignments_csv:
    mechanic_uuid = old_mechanic_id_to_uuid.get(row["mechanic_id"])
    project_uuid = old_project_id_to_uuid.get(row["project_id"])

    if not mechanic_uuid:
        print(f"  SKIP assignment {row['id']}: mechanic_id {row['mechanic_id']} not resolved")
        continue
    if not project_uuid:
        print(f"  SKIP assignment {row['id']}: project_id {row['project_id']} not resolved")
        continue

    payload = {
        "mechanic_id": mechanic_uuid,
        "project_id": project_uuid,
        "sequence": int(row["sequence"]),
        "start_date": row["start_date"],
        "end_date": row["end_date"],
    }
    response = supabase.table("assignments").insert(payload).execute()
    if not response.data:
        print(f"  ERROR inserting assignment {row['id']}")
    else:
        print(f"  Assignment {row['id']} -> {response.data[0]['id']}")

print("\nMigration complete.")
