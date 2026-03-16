import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic

import json
import logging

from database import (
    fetch_personnel,
    fetch_personnel_page,
    fetch_projects,
    fetch_projects_page,
    fetch_project_by_id,
    fetch_skills,
    fetch_assignments_by_scenario,
    fetch_assignments_enriched,
    fetch_overview_data,
    fetch_schedule_projects,
    fetch_available_personnel,
    fetch_master_scenario,
    fetch_scenarios,
    fetch_active_drafts,
    insert_personnel,
    update_personnel,
    delete_personnel,
    insert_project,
    update_project,
    delete_project,
    insert_skill,
    insert_assignment,
    delete_assignment,
    delete_assignments_by_project,
    delete_assignments_by_personnel,
    update_assignment,
    insert_scenario,
    update_scenario,
    copy_assignments_to_scenario,
    shift_project_assignments,
    bulk_insert_assignments,
    delete_assignments_by_scenario,
    delete_scenario as db_delete_scenario,
)

router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

MAX_ACTIVE_DRAFTS = 5

logger = logging.getLogger(__name__)

SCHEDULE_TOOL = {
    "name": "generate_schedule",
    "description": "Generate a complete draft schedule by creating assignments for personnel to projects. Only use this when the user explicitly asks to CREATE or GENERATE a schedule.",
    "input_schema": {
        "type": "object",
        "properties": {
            "draft_name": {
                "type": "string",
                "description": "A descriptive name for this draft schedule",
            },
            "assignments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "personnel_id": {"type": "string"},
                        "project_id": {"type": "string"},
                        "sequence": {"type": "integer"},
                        "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                        "assignment_type": {
                            "type": "string",
                            "enum": ["full", "cascading", "partial"],
                        },
                    },
                    "required": ["personnel_id", "project_id", "sequence", "start_date", "end_date", "assignment_type"],
                },
                "description": "List of personnel-to-project assignments",
            },
            "reasoning": {
                "type": "string",
                "description": "Brief explanation of the scheduling strategy used",
            },
        },
        "required": ["draft_name", "assignments", "reasoning"],
    },
}


def _execute_schedule_tool(tool_input: dict) -> dict:
    """Execute the generate_schedule tool: validate, create draft, insert assignments."""
    # Check draft limit
    active_drafts = fetch_active_drafts()
    if len(active_drafts) >= MAX_ACTIVE_DRAFTS:
        return {"success": False, "error": f"Maximum of {MAX_ACTIVE_DRAFTS} active drafts reached. Archive one first."}

    assignments = tool_input.get("assignments", [])
    if not assignments:
        return {"success": False, "error": "No assignments provided."}

    # Validate all personnel_id and project_id values exist
    personnel = fetch_personnel()
    projects = fetch_projects()
    valid_personnel_ids = {str(p["id"]) for p in personnel}
    valid_project_ids = {str(p["id"]) for p in projects}

    for a in assignments:
        if str(a["personnel_id"]) not in valid_personnel_ids:
            return {"success": False, "error": f"Invalid personnel_id: {a['personnel_id']}"}
        if str(a["project_id"]) not in valid_project_ids:
            return {"success": False, "error": f"Invalid project_id: {a['project_id']}"}

    # Create draft branched from master — copy existing assignments first
    master = fetch_master_scenario()
    try:
        new_scenario = insert_scenario({
            "name": tool_input["draft_name"],
            "status": "draft",
            "created_from": master["id"] if master else None,
        })
        scenario_id = new_scenario["id"]

        # Copy all existing master assignments so staffed projects stay intact
        if master:
            copy_assignments_to_scenario(master["id"], scenario_id)

        # Add Claude's new assignments on top
        result = bulk_insert_assignments(scenario_id, assignments)

        return {
            "success": True,
            "scenario_id": str(scenario_id),
            "scenario_name": tool_input["draft_name"],
            "assignments_created": result["inserted"],
        }
    except Exception as e:
        logger.exception("Failed to create AI schedule draft")
        # Try to archive the failed scenario if it was created
        try:
            if 'scenario_id' in locals():
                update_scenario(scenario_id, {
                    "archived_at": now_iso(),
                    "archived_reason": "failed_creation",
                })
        except Exception:
            pass
        return {"success": False, "error": f"Database error: {str(e)}"}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def _get_scenario_id(scenario_id: Optional[str]) -> Optional[str]:
    if scenario_id and scenario_id not in ("null", "undefined"):
        return scenario_id
    master = fetch_master_scenario()
    return master["id"] if master else None


# ── Models ─────────────────────────────────────────────────────────────────────

class PersonnelCreate(BaseModel):
    name: str
    skills: str


class PersonnelUpdate(BaseModel):
    name: Optional[str] = None
    skills: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    required_skills: str
    num_elevators: int
    contract_start_date: str
    duration_weeks: int
    award_status: str


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    required_skills: Optional[str] = None
    num_elevators: Optional[int] = None
    contract_start_date: Optional[str] = None
    duration_weeks: Optional[int] = None
    award_status: Optional[str] = None


class SkillCreate(BaseModel):
    skill: str


class AssignmentCreate(BaseModel):
    personnel_id: str
    project_id: str
    scenario_id: str
    sequence: int
    start_date: str
    end_date: str
    assignment_type: str = "full"


class AssignmentUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    assignment_type: Optional[str] = None


class ShiftScheduleRequest(BaseModel):
    new_start_date: str


class ScenarioCreate(BaseModel):
    name: str


class ChatRequest(BaseModel):
    messages: list[dict]


# ── Personnel ──────────────────────────────────────────────────────────────────

@router.get("/api/personnel")
async def get_personnel(scenario_id: Optional[str] = None):
    sid = _get_scenario_id(scenario_id)
    if sid:
        return fetch_personnel_page(sid)
    return fetch_personnel()


@router.post("/api/personnel")
async def create_personnel(personnel: PersonnelCreate):
    return insert_personnel(personnel.model_dump())


@router.delete("/api/personnel/{personnel_id}")
async def remove_personnel(personnel_id: str):
    delete_assignments_by_personnel(personnel_id)
    delete_personnel(personnel_id)
    return {"success": True}


@router.patch("/api/personnel/{personnel_id}")
async def patch_personnel(personnel_id: str, data: PersonnelUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = update_personnel(personnel_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Personnel not found")
    return result


# ── Projects ───────────────────────────────────────────────────────────────────

@router.get("/api/projects")
async def get_projects(scenario_id: Optional[str] = None):
    sid = _get_scenario_id(scenario_id)
    if sid:
        return fetch_projects_page(sid)
    return fetch_projects()


@router.post("/api/projects")
async def create_project(project: ProjectCreate):
    data = project.model_dump()
    start = datetime.strptime(data["contract_start_date"], "%Y-%m-%d")
    end = start + timedelta(weeks=data["duration_weeks"])
    data["contract_end_date"] = end.strftime("%Y-%m-%d")
    return insert_project(data)


@router.delete("/api/projects/{project_id}")
async def remove_project(project_id: str):
    delete_assignments_by_project(project_id)
    delete_project(project_id)
    return {"success": True}


@router.patch("/api/projects/{project_id}")
async def patch_project(project_id: str, data: ProjectUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(400, "No fields to update")
    # Recalculate end date if start or duration changed
    if "contract_start_date" in updates or "duration_weeks" in updates:
        start_str = updates.get("contract_start_date")
        weeks = updates.get("duration_weeks")
        if not start_str or not weeks:
            current = fetch_project_by_id(project_id)
            if not current:
                raise HTTPException(404, "Project not found")
            start_str = start_str or str(current["contract_start_date"])
            weeks = weeks or current["duration_weeks"]
        start = datetime.strptime(start_str, "%Y-%m-%d")
        updates["contract_end_date"] = (start + timedelta(weeks=weeks)).strftime("%Y-%m-%d")
    result = update_project(project_id, updates)
    if not result:
        raise HTTPException(404, "Project not found")
    return result


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
    sid = _get_scenario_id(scenario_id)
    if sid:
        return fetch_assignments_enriched(sid)
    return []


@router.get("/api/assignments/overview")
async def get_overview_assignments(scenario_id: Optional[str] = None):
    sid = _get_scenario_id(scenario_id)
    if sid:
        return fetch_overview_data(sid)
    return []


@router.get("/api/assignments/schedule-projects")
async def get_schedule_projects(scenario_id: Optional[str] = None):
    sid = _get_scenario_id(scenario_id)
    if sid:
        return fetch_schedule_projects(sid)
    return []


@router.get("/api/assignments/available-personnel")
async def get_available_personnel(
    scenario_id: str,
    project_id: str,
    project_start: str,
    project_end: str,
):
    return fetch_available_personnel(scenario_id, project_id, project_start, project_end)


@router.delete("/api/assignments/{assignment_id}")
async def remove_assignment(assignment_id: str):
    delete_assignment(assignment_id)
    return {"success": True}


@router.patch("/api/assignments/{assignment_id}")
async def patch_assignment(assignment_id: str, data: AssignmentUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = update_assignment(assignment_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return result


@router.post("/api/assignments")
async def create_assignment(assignment: AssignmentCreate):
    return insert_assignment(assignment.model_dump())


@router.post("/api/projects/{project_id}/shift-schedule")
async def shift_schedule(project_id: str, data: ShiftScheduleRequest, scenario_id: Optional[str] = None):
    sid = _get_scenario_id(scenario_id)
    if not sid:
        raise HTTPException(400, "No scenario found")
    result = shift_project_assignments(sid, project_id, data.new_start_date)
    return result


# ── Scenarios ──────────────────────────────────────────────────────────────────

@router.get("/api/scenarios")
async def get_scenarios():
    scenarios = fetch_scenarios()
    if not scenarios:
        insert_scenario({"name": "Master Schedule", "status": "master"})
        scenarios = fetch_scenarios()
    return scenarios


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
async def remove_scenario(scenario_id: str):
    delete_assignments_by_scenario(scenario_id)
    db_delete_scenario(scenario_id)
    return {"success": True}


# ── Chat ───────────────────────────────────────────────────────────────────────

@router.post("/api/chat")
async def chat(request: ChatRequest):
    master = fetch_master_scenario()
    sid = master["id"] if master else None

    projects = fetch_projects_page(sid) if sid else fetch_projects()
    personnel = fetch_personnel_page(sid) if sid else fetch_personnel()
    assignments = fetch_assignments_enriched(sid) if sid else []

    projects_text = "\n".join([
        f"- {p['name']} (id:{p['id']}): requires [{p['required_skills']}], {p['num_elevators']} elevators, "
        f"contract {p['contract_start_date']} to {p['contract_end_date']}, duration {p['duration_weeks']} weeks, "
        f"award: {p['award_status']}, schedule: {p.get('schedule_status', 'unknown')}"
        + (f", actual dates: {p.get('actual_start_date')} to {p.get('actual_end_date')}" if p.get('actual_start_date') else "")
        for p in projects
    ])

    personnel_text = "\n".join([
        f"- {p['name']} (id:{p['id']}): skills [{p['skills']}], status: {p.get('availability_status', 'unknown')}, "
        f"next available: {p.get('next_available_date', 'unknown')}"
        + (f", current project: {p['current_project_name']}" if p.get('current_project_name') else "")
        + (f", next project: {p['next_project_name']} starting {p['next_assignment_start']}" if p.get('next_project_name') else "")
        for p in personnel
    ])

    assignments_text = "\n".join([
        f"- {a.get('personnel_name', a['personnel_id'])} -> "
        f"{a.get('project_name', a['project_id'])}: "
        f"sequence {a['sequence']}, {a['start_date']} to {a['end_date']}, type: {a.get('assignment_type', 'full')}"
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
Be concise and helpful. Today's date is {now_iso()}.

Avoid using emojis unless they convey unambiguous meaning in context.
In particular, do not use visual indicators (e.g. checkmarks) for partial matches — for example, a skill match alone does not mean a mechanic is available or suitable for a job.
Only use a positive indicator when all relevant conditions are met.

If I tell you to give me a recommendation for how to schedule a bunch of projects, just give me a simple output via:
Mechanic Name (Available Date) --> Project Name (Contract Start Date).
Make sure to ask if I want to match skills or not.

SCHEDULE GENERATION INSTRUCTIONS:
You have a tool called "generate_schedule" that creates a draft schedule in the system.
Only use this tool when the user EXPLICITLY asks you to CREATE, GENERATE, or BUILD a schedule.
Do NOT use the tool for questions, recommendations, or analysis — only for actual schedule creation.

When generating a schedule:
- IMPORTANT: Only schedule UNSCHEDULED projects (schedule_status = 'Unscheduled'). Projects that are already 'Active' or 'Scheduled' must NOT be re-scheduled — their existing assignments will be preserved automatically.
- When considering personnel availability, account for their EXISTING assignments listed above. Do not create overlapping date ranges for the same person.
- Match personnel skills to project required_skills. If a person's skills overlap with the project's required skills, they are a candidate.
- Respect contract_start_date and contract_end_date bounds for each project.
- Use the project's duration_weeks to calculate assignment length (start_date + duration_weeks = end_date).
- Number NEW assignments sequentially per person, continuing from their highest existing sequence number.
- Default assignment_type to "full".
- Only schedule projects with award_status = 'awarded' unless the user explicitly asks otherwise.
- Give the draft a descriptive name reflecting the strategy used.
- Before calling the tool, briefly explain your scheduling strategy to the user.
- After the tool executes, summarize what was created (how many assignments, which personnel/projects).
"""

    # First Claude API call — with tool definition
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=request.messages,
        tools=[SCHEDULE_TOOL],
    )

    # Check if Claude wants to use a tool
    tool_use_block = None
    text_blocks = []
    for block in response.content:
        if block.type == "tool_use":
            tool_use_block = block
        elif block.type == "text":
            text_blocks.append(block.text)

    # No tool use — return text response as before
    if not tool_use_block:
        return {"response": "\n".join(text_blocks) if text_blocks else ""}

    # Execute the tool
    tool_result = _execute_schedule_tool(tool_use_block.input)

    # Build the messages for the second Claude call (include tool result)
    follow_up_messages = list(request.messages) + [
        {"role": "assistant", "content": [b.model_dump() for b in response.content]},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": json.dumps(tool_result),
                }
            ],
        },
    ]

    # Second Claude call — get summary text
    summary_response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system_prompt,
        messages=follow_up_messages,
        tools=[SCHEDULE_TOOL],
    )

    summary_text_parts = []
    for block in summary_response.content:
        if block.type == "text":
            summary_text_parts.append(block.text)

    # Combine any pre-tool text with the summary
    all_text = []
    if text_blocks:
        all_text.extend(text_blocks)
    if summary_text_parts:
        all_text.extend(summary_text_parts)

    result = {"response": "\n\n".join(all_text) if all_text else "Schedule generation completed."}

    # If schedule was created successfully, include metadata for frontend
    if tool_result.get("success"):
        result["schedule_created"] = True
        result["scenario_id"] = tool_result["scenario_id"]
        result["scenario_name"] = tool_result["scenario_name"]

    return result
