import os
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_RELAI_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_RELAI_SECRET_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    missing = [k for k, v in {"SUPABASE_RELAI_URL": SUPABASE_URL, "SUPABASE_RELAI_SECRET_KEY": SUPABASE_KEY}.items() if not v]
    raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_mechanics():
    return supabase.table("mechanics").select("*").execute().data


def fetch_projects():
    return supabase.table("projects").select("*").execute().data


def fetch_skills():
    return supabase.table("skills").select("*").execute().data


def fetch_assignments():
    return supabase.table("assignments").select("*").execute().data


def insert_mechanic(data: dict):
    return supabase.table("mechanics").insert(data).execute()


def insert_project(data: dict):
    return supabase.table("projects").insert(data).execute()


def insert_skill(data: dict):
    return supabase.table("skills").insert(data).execute()


def insert_assignment(data: dict):
    return supabase.table("assignments").insert(data).execute()
