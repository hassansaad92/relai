import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic

from database import (
    fetch_personnel,
    fetch_projects,
    fetch_skills,
    fetch_assignments,
    insert_personnel,
    insert_project,
    insert_skill,
    insert_assignment,
)

router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


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
    sequence: int
    start_date: str
    end_date: str


class ChatRequest(BaseModel):
    messages: list[dict]  # [{role: str, content: str}]


@router.get("/api/personnel")
async def get_personnel():
    return fetch_personnel()


@router.get("/api/projects")
async def get_projects():
    return fetch_projects()


@router.get("/api/skills")
async def get_skills():
    return fetch_skills()


@router.get("/api/assignments")
async def get_assignments():
    return fetch_assignments()


@router.post("/api/personnel")
async def create_personnel(personnel: PersonnelCreate):
    response = insert_personnel(personnel.model_dump())
    print("INSERT personnel response:", response)
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create personnel")
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
    personnel = fetch_personnel()
    assignments = fetch_assignments()

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
