import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic

from database import (
    fetch_mechanics,
    fetch_projects,
    fetch_skills,
    fetch_assignments,
    insert_mechanic,
    insert_project,
    insert_skill,
    insert_assignment,
)

router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class MechanicCreate(BaseModel):
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
    mechanic_id: str
    project_id: str
    sequence: int
    start_date: str
    end_date: str


class ChatRequest(BaseModel):
    messages: list[dict]  # [{role: str, content: str}]


@router.get("/api/mechanics")
async def get_mechanics():
    return fetch_mechanics()


@router.get("/api/projects")
async def get_projects():
    return fetch_projects()


@router.get("/api/skills")
async def get_skills():
    return fetch_skills()


@router.get("/api/assignments")
async def get_assignments():
    return fetch_assignments()


@router.post("/api/mechanics")
async def create_mechanic(mechanic: MechanicCreate):
    response = insert_mechanic(mechanic.model_dump())
    print("INSERT mechanics response:", response)
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create mechanic")
    return response.data[0]


@router.post("/api/projects")
async def create_project(project: ProjectCreate):
    response = insert_project(project.model_dump())
    print("INSERT projects response:", response)
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create project")
    return response.data[0]


@router.post("/api/skills")
async def create_skill(skill: SkillCreate):
    response = insert_skill(skill.model_dump())
    print("INSERT skills response:", response)
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create skill")
    return response.data[0]


@router.post("/api/assignments")
async def create_assignment(assignment: AssignmentCreate):
    response = insert_assignment(assignment.model_dump())
    print("INSERT assignments response:", response)
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create assignment")
    return response.data[0]


@router.post("/api/chat")
async def chat(request: ChatRequest):
    projects = fetch_projects()
    mechanics = fetch_mechanics()
    assignments = fetch_assignments()

    projects_by_id = {p['id']: p for p in projects}
    mechanics_by_id = {m['id']: m for m in mechanics}

    projects_text = "\n".join([
        f"- {p['name']} (id:{p['id']}): requires [{p['required_skills']}], {p['num_elevators']} elevators, "
        f"starts {p['start_date']}, duration {p['duration_weeks']} weeks, status: {p['status']}"
        for p in projects
    ])

    mechanics_text = "\n".join([
        f"- {m['name']} (id:{m['id']}): skills [{m['skills']}], status: {m['availability_status']}, available: {m['available_date']}"
        for m in mechanics
    ])

    assignments_text = "\n".join([
        f"- {mechanics_by_id.get(a['mechanic_id'], {}).get('name', a['mechanic_id'])} -> "
        f"{projects_by_id.get(a['project_id'], {}).get('name', a['project_id'])}: "
        f"sequence {a['sequence']}, {a['start_date']} to {a['end_date']}"
        for a in assignments
    ])

    system_prompt = f"""You are a helpful scheduling assistant for an elevator installation company.
You have real-time access to the following data from the database:

PROJECTS:
{projects_text}

MECHANICS:
{mechanics_text}

ASSIGNMENTS (confirmed mechanic-to-project assignments):
{assignments_text}

Answer questions about projects, scheduling, resource allocation, and team assignments based on this data.
When asked about a mechanic's next project, look up their assignments directly.
Be concise and helpful. Today's date is 2026-03-08."""

    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=request.messages,
    )
    return {"response": response.content[0].text}
