import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_RELAI_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_RELAI_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    missing = [k for k, v in {"SUPABASE_RELAI_URL": SUPABASE_URL, "SUPABASE_RELAI_SECRET_KEY": SUPABASE_KEY}.items() if not v]
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Personnel ──────────────────────────────────────────────────────────────────

def fetch_personnel():
    return supabase.table("personnel").select("*").execute().data


def insert_personnel(data: dict):
    return supabase.table("personnel").insert(data).execute()


# ── Projects ───────────────────────────────────────────────────────────────────

def fetch_projects():
    return supabase.table("projects").select("*").execute().data


def insert_project(data: dict):
    return supabase.table("projects").insert(data).execute()


# ── Skills ─────────────────────────────────────────────────────────────────────

def fetch_skills():
    return supabase.table("skills").select("*").execute().data


def insert_skill(data: dict):
    return supabase.table("skills").insert(data).execute()


# ── Assignments ────────────────────────────────────────────────────────────────

def fetch_assignments_by_scenario(scenario_id: str):
    return supabase.table("assignments").select("*").eq("scenario_id", scenario_id).execute().data


def insert_assignment(data: dict):
    return supabase.table("assignments").insert(data).execute()


def copy_assignments_to_scenario(from_scenario_id: str, to_scenario_id: str):
    source = supabase.table("assignments").select("*").eq("scenario_id", from_scenario_id).execute().data
    if not source:
        return
    new_rows = [
        {k: v for k, v in row.items() if k not in ("id", "created_at", "scenario_id")} | {"scenario_id": to_scenario_id}
        for row in source
    ]
    return supabase.table("assignments").insert(new_rows).execute()


# ── Scenarios ──────────────────────────────────────────────────────────────────

def fetch_scenarios():
    return supabase.table("scenarios").select("*").is_("archived_at", "null").order("created_at").execute().data


def fetch_master_scenario():
    results = supabase.table("scenarios").select("*").eq("status", "master").is_("archived_at", "null").execute().data
    return results[0] if results else None


def fetch_active_drafts():
    return supabase.table("scenarios").select("*").eq("status", "draft").is_("archived_at", "null").execute().data


def insert_scenario(data: dict):
    return supabase.table("scenarios").insert(data).execute()


def update_scenario(scenario_id: str, data: dict):
    return supabase.table("scenarios").update(data).eq("id", scenario_id).execute()
