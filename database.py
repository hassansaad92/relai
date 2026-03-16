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
    user = os.environ.get("SUPABASE_RELAI_DB_USER", "postgres.grkdykxrckzusbgkgsuk")
    port = os.environ.get("SUPABASE_RELAI_DB_PORT", "6543")
    return f"postgresql://{user}:{password}@{host}:{port}/postgres"


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
        cur.execute("SELECT * FROM projects ORDER BY contract_start_date")
        return [dict(r) for r in cur.fetchall()]


def fetch_projects_page(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute(_load_sql("projects_list"), {"scenario_id": scenario_id})
        return [dict(r) for r in cur.fetchall()]


def delete_project(project_id: str):
    with _cursor() as (_, cur):
        cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))


def update_project(project_id: str, data: dict):
    with _cursor() as (_, cur):
        set_clause = ", ".join(f"{k} = %({k})s" for k in data.keys())
        cur.execute(
            f"UPDATE projects SET {set_clause} WHERE id = %(id)s RETURNING *",
            {**data, "id": project_id},
        )
        row = cur.fetchone()
        return dict(row) if row else None


def fetch_project_by_id(project_id: str):
    with _cursor() as (_, cur):
        cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
        row = cur.fetchone()
        return dict(row) if row else None


def insert_project(data: dict):
    with _cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO projects (name, contract_start_date, contract_end_date, duration_weeks, num_elevators, required_skills, award_status)
            VALUES (%(name)s, %(contract_start_date)s, %(contract_end_date)s, %(duration_weeks)s, %(num_elevators)s, %(required_skills)s, %(award_status)s)
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


def shift_project_assignments(scenario_id: str, project_id: str, new_start_date: str):
    from datetime import date, timedelta
    new_start = date.fromisoformat(new_start_date)
    with _cursor() as (_, cur):
        cur.execute(
            "SELECT MIN(start_date) AS min_start FROM assignments WHERE scenario_id = %s AND project_id = %s",
            (scenario_id, project_id),
        )
        row = cur.fetchone()
        if not row or not row["min_start"]:
            return {"shifted": 0, "delta_days": 0}
        min_start = row["min_start"]
        delta = (new_start - min_start).days
        if delta == 0:
            return {"shifted": 0, "delta_days": 0}
        cur.execute(
            """
            UPDATE assignments
            SET start_date = start_date + %s * INTERVAL '1 day',
                end_date = end_date + %s * INTERVAL '1 day'
            WHERE scenario_id = %s AND project_id = %s
            """,
            (delta, delta, scenario_id, project_id),
        )
        return {"shifted": cur.rowcount, "delta_days": delta}


def bulk_insert_assignments(scenario_id: str, assignments_list: list[dict]):
    with _cursor() as (_, cur):
        for a in assignments_list:
            cur.execute(
                """
                INSERT INTO assignments (personnel_id, project_id, scenario_id, sequence, start_date, end_date, assignment_type)
                VALUES (%(personnel_id)s, %(project_id)s, %(scenario_id)s, %(sequence)s, %(start_date)s, %(end_date)s, %(assignment_type)s)
                """,
                {**a, "scenario_id": scenario_id},
            )
        return {"inserted": len(assignments_list)}


def delete_assignments_by_scenario(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute("DELETE FROM assignments WHERE scenario_id = %s", (scenario_id,))
        return {"deleted": cur.rowcount}


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


def delete_scenario(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute("DELETE FROM scenarios WHERE id = %s", (scenario_id,))


def archive_scenario_assignments(scenario_id: str, scenario_name: str):
    """Copy assignments to archive, then delete originals. Single transaction."""
    with _cursor() as (_, cur):
        cur.execute(
            """
            INSERT INTO assignments_archive
                (original_assignment_id, personnel_id, project_id, scenario_id, scenario_name, sequence, start_date, end_date, assignment_type)
            SELECT id, personnel_id, project_id, scenario_id, %s, sequence, start_date, end_date, assignment_type
            FROM assignments
            WHERE scenario_id = %s
            """,
            (scenario_name, scenario_id),
        )
        archived = cur.rowcount
        cur.execute("DELETE FROM assignments WHERE scenario_id = %s", (scenario_id,))
        return {"archived": archived}


def fetch_archived_scenarios():
    with _cursor() as (_, cur):
        cur.execute(
            """
            SELECT scenario_id, scenario_name, MAX(archived_at) AS archived_at, COUNT(*) AS assignment_count
            FROM assignments_archive
            GROUP BY scenario_id, scenario_name
            ORDER BY MAX(archived_at) DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]


def fetch_archived_assignments(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute(
            """
            SELECT aa.*, p.name AS personnel_name, pr.name AS project_name
            FROM assignments_archive aa
            LEFT JOIN personnel p ON p.id = aa.personnel_id
            LEFT JOIN projects pr ON pr.id = aa.project_id
            WHERE aa.scenario_id = %s
            ORDER BY p.name, aa.start_date
            """,
            (scenario_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def fetch_ai_scheduling_context(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute(_load_sql("ai_scheduling_context"), {"scenario_id": scenario_id})
        return [dict(r) for r in cur.fetchall()]


def fetch_ai_unscheduled_projects(scenario_id: str):
    with _cursor() as (_, cur):
        cur.execute(_load_sql("ai_unscheduled_projects"), {"scenario_id": scenario_id})
        return [dict(r) for r in cur.fetchall()]


def update_scenario(scenario_id: str, data: dict):
    with _cursor() as (_, cur):
        set_clause = ", ".join(f"{k} = %({k})s" for k in data.keys())
        cur.execute(
            f"UPDATE scenarios SET {set_clause} WHERE id = %(id)s",
            {**data, "id": scenario_id},
        )
