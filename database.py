import os
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

_pool: ThreadedConnectionPool | None = None

QUERIES_DIR = Path(__file__).parent / "queries"


@lru_cache(maxsize=32)
def _load_sql(name: str) -> str:
    return (QUERIES_DIR / f"{name}.sql").read_text()


def _dsn():
    host = os.environ.get("SUPABASE_RELAI_DB_HOST")
    password = os.environ.get("SUPABASE_RELAI_DB_PASSWORD")
    if not host:
        raise RuntimeError("Missing environment variable: SUPABASE_RELAI_DB_HOST")
    if not password:
        raise RuntimeError("Missing environment variable: SUPABASE_RELAI_DB_PASSWORD")
    return f"postgresql://postgres:{password}@{host}:5432/postgres"


def init_pool():
    global _pool
    _pool = ThreadedConnectionPool(1, 10, _dsn(), cursor_factory=psycopg2.extras.RealDictCursor)


def close_pool():
    global _pool
    if _pool:
        _pool.closeall()
        _pool = None


@contextmanager
def _cursor():
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    conn = _pool.getconn()
    try:
        cur = conn.cursor()
        yield conn, cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        _pool.putconn(conn)


# ── Personnel ──────────────────────────────────────────────────────────────────

def fetch_personnel():
    with _cursor() as (_, cur):
        cur.execute("SELECT * FROM personnel ORDER BY name")
        return [dict(r) for r in cur.fetchall()]


def fetch_personnel_page(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute(_load_sql("personnel_list"), {"scenario_id": scenario_id})
        return [dict(r) for r in cur.fetchall()]


def insert_personnel(data: dict):
    with _cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO personnel (name, skills)
            VALUES (%(name)s, %(skills)s)
            RETURNING *
            """,
            data,
        )
        return dict(cur.fetchone())


def delete_personnel(personnel_id: str):
    with _cursor() as (_, cur):
        cur.execute("DELETE FROM personnel WHERE id = %s", (personnel_id,))


def update_personnel(personnel_id: str, data: dict):
    with _cursor() as (_, cur):
        set_clause = ", ".join(f"{k} = %({k})s" for k in data.keys())
        cur.execute(
            f"UPDATE personnel SET {set_clause} WHERE id = %(id)s RETURNING *",
            {**data, "id": personnel_id},
        )
        row = cur.fetchone()
        return dict(row) if row else None


# ── Projects ───────────────────────────────────────────────────────────────────

def fetch_projects():
    with _cursor() as (_, cur):
        cur.execute("SELECT * FROM projects ORDER BY requested_start_date")
        return [dict(r) for r in cur.fetchall()]


def fetch_projects_page(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute(_load_sql("projects_list"), {"scenario_id": scenario_id})
        return [dict(r) for r in cur.fetchall()]


def delete_project(project_id: str):
    with _cursor() as (_, cur):
        cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))


def insert_project(data: dict):
    with _cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO projects (name, requested_start_date, requested_end_date, duration_weeks, num_elevators, required_skills, award_status)
            VALUES (%(name)s, %(requested_start_date)s, %(requested_end_date)s, %(duration_weeks)s, %(num_elevators)s, %(required_skills)s, %(award_status)s)
            RETURNING *
            """,
            data,
        )
        return dict(cur.fetchone())


# ── Skills ─────────────────────────────────────────────────────────────────────

def fetch_skills():
    with _cursor() as (_, cur):
        cur.execute("SELECT * FROM skills")
        return [dict(r) for r in cur.fetchall()]


def insert_skill(data: dict):
    with _cursor() as (_, cur):
        cur.execute(
            "INSERT INTO skills (skill) VALUES (%(skill)s) RETURNING *",
            data,
        )
        return dict(cur.fetchone())


# ── Assignments ────────────────────────────────────────────────────────────────

def fetch_assignments_by_scenario(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute("SELECT * FROM assignments WHERE scenario_id = %s", (scenario_id,))
        return [dict(r) for r in cur.fetchall()]


def fetch_assignments_enriched(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute(_load_sql("assignments_by_scenario"), {"scenario_id": scenario_id})
        return [dict(r) for r in cur.fetchall()]


def fetch_overview_data(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute(_load_sql("overview_gantt"), {"scenario_id": scenario_id})
        return [dict(r) for r in cur.fetchall()]


def fetch_schedule_projects(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute(_load_sql("schedule_projects"), {"scenario_id": scenario_id})
        return [dict(r) for r in cur.fetchall()]


def fetch_available_personnel(scenario_id: str, project_id: str, project_start: str, project_end: str):
    with _cursor() as (_, cur):
        cur.execute(_load_sql("available_personnel"), {
            "scenario_id": scenario_id,
            "project_id": project_id,
            "project_start": project_start,
            "project_end": project_end,
        })
        return [dict(r) for r in cur.fetchall()]


def insert_assignment(data: dict):
    with _cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO assignments (personnel_id, project_id, scenario_id, sequence, start_date, end_date, assignment_type)
            VALUES (%(personnel_id)s, %(project_id)s, %(scenario_id)s, %(sequence)s, %(start_date)s, %(end_date)s, %(assignment_type)s)
            RETURNING *
            """,
            data,
        )
        return dict(cur.fetchone())


def delete_assignment(assignment_id: str):
    with _cursor() as (_, cur):
        cur.execute("DELETE FROM assignments WHERE id = %s", (assignment_id,))


def delete_assignments_by_project(project_id: str):
    with _cursor() as (_, cur):
        cur.execute("DELETE FROM assignments WHERE project_id = %s", (project_id,))


def delete_assignments_by_personnel(personnel_id: str):
    with _cursor() as (_, cur):
        cur.execute("DELETE FROM assignments WHERE personnel_id = %s", (personnel_id,))


def update_assignment(assignment_id: str, data: dict):
    with _cursor() as (_, cur):
        set_clause = ", ".join(f"{k} = %({k})s" for k in data.keys())
        cur.execute(
            f"UPDATE assignments SET {set_clause} WHERE id = %(id)s RETURNING *",
            {**data, "id": assignment_id},
        )
        row = cur.fetchone()
        return dict(row) if row else None


def copy_assignments_to_scenario(from_scenario_id: str, to_scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO assignments (personnel_id, project_id, scenario_id, sequence, start_date, end_date, assignment_type)
            SELECT personnel_id, project_id, %s, sequence, start_date, end_date, assignment_type
            FROM assignments
            WHERE scenario_id = %s
            """,
            (to_scenario_id, from_scenario_id),
        )


# ── Scenarios ──────────────────────────────────────────────────────────────────

def fetch_scenarios():
    with _cursor() as (_, cur):
        cur.execute(
            "SELECT * FROM scenarios WHERE archived_at IS NULL ORDER BY created_at"
        )
        return [dict(r) for r in cur.fetchall()]


def fetch_master_scenario():
    with _cursor() as (_, cur):
        cur.execute(
            "SELECT * FROM scenarios WHERE status = 'master' AND archived_at IS NULL LIMIT 1"
        )
        row = cur.fetchone()
        return dict(row) if row else None


def fetch_active_drafts():
    with _cursor() as (_, cur):
        cur.execute(
            "SELECT * FROM scenarios WHERE status = 'draft' AND archived_at IS NULL"
        )
        return [dict(r) for r in cur.fetchall()]


def insert_scenario(data: dict):
    with _cursor() as (_, cur):
        cols = ", ".join(data.keys())
        placeholders = ", ".join(f"%({k})s" for k in data.keys())
        cur.execute(
            f"INSERT INTO scenarios ({cols}) VALUES ({placeholders}) RETURNING *",
            data,
        )
        return dict(cur.fetchone())


def update_scenario(scenario_id: str, data: dict):
    with _cursor() as (_, cur):
        set_clause = ", ".join(f"{k} = %({k})s" for k in data.keys())
        cur.execute(
            f"UPDATE scenarios SET {set_clause} WHERE id = %(id)s",
            {**data, "id": scenario_id},
        )
