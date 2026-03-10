import os
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

_pool: ThreadedConnectionPool | None = None


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
        cur.execute("SELECT * FROM personnel")
        return [dict(r) for r in cur.fetchall()]


def insert_personnel(data: dict):
    with _cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO personnel (name, skills, availability_status, available_date)
            VALUES (%(name)s, %(skills)s, %(availability_status)s, %(available_date)s)
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
        cur.execute("SELECT * FROM projects")
        return [dict(r) for r in cur.fetchall()]


def delete_project(project_id: str):
    with _cursor() as (_, cur):
        cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))


def insert_project(data: dict):
    with _cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO projects (name, start_date, duration_weeks, num_elevators, required_skills, award_status, schedule_status)
            VALUES (%(name)s, %(start_date)s, %(duration_weeks)s, %(num_elevators)s, %(required_skills)s, %(award_status)s, %(schedule_status)s)
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


def insert_assignment(data: dict):
    with _cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO assignments (personnel_id, project_id, scenario_id, sequence, start_date, end_date)
            VALUES (%(personnel_id)s, %(project_id)s, %(scenario_id)s, %(sequence)s, %(start_date)s, %(end_date)s)
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
            INSERT INTO assignments (personnel_id, project_id, scenario_id, sequence, start_date, end_date)
            SELECT personnel_id, project_id, %s, sequence, start_date, end_date
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
