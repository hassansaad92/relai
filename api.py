import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic

from database import (
    fetch_personnel,
    fetch_projects,
    fetch_skills,
    fetch_assignments_by_scenario,
    fetch_master_scenario,
    fetch_scenarios,
    fetch_active_drafts,
    insert_personnel,
    insert_project,
    insert_skill,
    insert_assignment,
    delete_assignment,
    insert_scenario,
    update_scenario,
    copy_assignments_to_scenario,
)

router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

MAX_ACTIVE_DRAFTS = 5


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ── Models ─────────────────────────────────────────────────────────────────────

class PersonnelCreate(BaseModel):
    name: str
    skills: str
    availability_status: str
    available_date: str


class ProjectCreate(BaseModel):
    name: str
    required_skills: str
    num_elevators: int
    start_date: str
    duration_weeks: int
    status: str


class SkillCreate(BaseModel):
    skill: str


class AssignmentCreate(BaseModel):
    personnel_id: str
    project_id: str
    scenario_id: str
    sequence: int
    start_date: str
    end_date: str


class ScenarioCreate(BaseModel):
    name: str


class ChatRequest(BaseModel):
    messages: list[dict]


# ── Personnel ──────────────────────────────────────────────────────────────────

@router.get("/api/personnel")
async def get_personnel():
    return fetch_personnel()


@router.post("/api/personnel")
async def create_personnel(personnel: PersonnelCreate):
    return insert_personnel(personnel.model_dump())


# ── Projects ───────────────────────────────────────────────────────────────────

@router.get("/api/projects")
async def get_projects():
    return fetch_projects()


@router.post("/api/projects")
async def create_project(project: ProjectCreate):
    return insert_project(project.model_dump())


# ── Skills ─────────────────────────────────────────────────────────────────────

@router.get("/api/skills")
async def get_skills():
    return fetch_skills()


@router.post("/api/skills")
async def create_skill(skill: SkillCreate):
    return insert_skill(skill.model_dump())


# ── Assignments ────────────────────────────────────────────────────────────────

@router.get("/api/assignments")
async def get_assignments(scenario_id: Optional[str] = None):
    if scenario_id:
        return fetch_assignments_by_scenario(scenario_id)
    master = fetch_master_scenario()
    if master:
        return fetch_assignments_by_scenario(master["id"])
    return []


@router.delete("/api/assignments/{assignment_id}")
async def remove_assignment(assignment_id: str):
    delete_assignment(assignment_id)
    return {"success": True}


@router.post("/api/assignments")
async def create_assignment(assignment: AssignmentCreate):
    return insert_assignment(assignment.model_dump())


# ── Scenarios ──────────────────────────────────────────────────────────────────

@router.get("/api/scenarios")
async def get_scenarios():
    return fetch_scenarios()


@router.post("/api/scenarios")
async def create_draft(scenario: ScenarioCreate):
    active_drafts = fetch_active_drafts()
    if len(active_drafts) >= MAX_ACTIVE_DRAFTS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum of {MAX_ACTIVE_DRAFTS} active drafts reached. Archive one before creating a new draft."
        )

    master = fetch_master_scenario()
    if not master:
        raise HTTPException(status_code=404, detail="No master scenario found.")

    new_scenario = insert_scenario({
        "name": scenario.name,
        "status": "draft",
        "created_from": master["id"],
    })
    copy_assignments_to_scenario(master["id"], new_scenario["id"])
    return new_scenario


@router.post("/api/scenarios/{scenario_id}/promote")
async def promote_scenario(scenario_id: str):
    now = now_iso()
    master = fetch_master_scenario()
    if master:
        update_scenario(master["id"], {
            "status": "draft",
            "archived_at": now,
            "archived_reason": "superseded",
            "demoted_from_master_at": now,
        })
    update_scenario(scenario_id, {
        "status": "master",
        "promoted_to_master_at": now,
    })
    return {"success": True}


@router.delete("/api/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: str):
    update_scenario(scenario_id, {
        "archived_at": now_iso(),
        "archived_reason": "deleted",
    })
    return {"success": True}


# ── Chat ───────────────────────────────────────────────────────────────────────

@router.post("/api/chat")
async def chat(request: ChatRequest):
    projects = fetch_projects()
    personnel = fetch_personnel()
    master = fetch_master_scenario()
    assignments = fetch_assignments_by_scenario(master["id"]) if master else []

    projects_by_id = {p['id']: p for p in projects}
    personnel_by_id = {p['id']: p for p in personnel}

    projects_text = "\n".join([
        f"- {p['name']} (id:{p['id']}): requires [{p['required_skills']}], {p['num_elevators']} elevators, "
        f"starts {p['start_date']}, duration {p['duration_weeks']} weeks, status: {p['status']}"
        for p in projects
    ])

    personnel_text = "\n".join([
        f"- {p['name']} (id:{p['id']}): skills [{p['skills']}], status: {p['availability_status']}, available: {p['available_date']}"
        for p in personnel
    ])

    assignments_text = "\n".join([
        f"- {personnel_by_id.get(a['personnel_id'], {}).get('name', a['personnel_id'])} -> "
        f"{projects_by_id.get(a['project_id'], {}).get('name', a['project_id'])}: "
        f"sequence {a['sequence']}, {a['start_date']} to {a['end_date']}"
        for a in assignments
    ])

    system_prompt = f"""You are a helpful scheduling assistant for an elevator installation company.
You have real-time access to the following data from the database:

PROJECTS:
{projects_text}

PERSONNEL:
{personnel_text}

ASSIGNMENTS (confirmed personnel-to-project assignments):
{assignments_text}

Answer questions about projects, scheduling, resource allocation, and team assignments based on this data.
When asked about a personnel member's next project, look up their assignments directly.
Be concise and helpful. Today's date is 2026-03-08."""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=request.messages,
    )
    return {"response": response.content[0].text}
