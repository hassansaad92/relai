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
    fetch_ai_scheduling_context,
    fetch_ai_unscheduled_projects,
    fetch_home_upcoming,
    fetch_home_project_stats,
    fetch_home_personnel_stats,
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
    cascade_assignment_end_date,
    bulk_insert_assignments,
    delete_assignments_by_scenario,
    delete_scenario as db_delete_scenario,
    archive_scenario_assignments,
    fetch_archived_scenarios,
    fetch_archived_assignments,
)

router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

MAX_ACTIVE_DRAFTS = 1

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


def _execute_schedule_tool(tool_input: dict, is_tweaking: bool = False) -> dict:
    """Execute the generate_schedule tool: validate, create draft, insert assignments."""
    # If tweaking, delete the existing draft first to make room
    if is_tweaking:
        active_drafts = fetch_active_drafts()
        for draft in active_drafts:
            delete_assignments_by_scenario(draft["id"])
            db_delete_scenario(draft["id"])
    else:
        # Check draft limit
        active_drafts = fetch_active_drafts()
        if len(active_drafts) >= MAX_ACTIVE_DRAFTS:
            return {"success": False, "error": "A draft already exists. Delete or promote it first."}

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


def _build_ai_context(scenario_id: str) -> str:
    """Build pre-computed scheduling context string for the AI system prompt."""
    rows = fetch_ai_scheduling_context(scenario_id)
    unscheduled = fetch_ai_unscheduled_projects(scenario_id)

    # Group by personnel
    from collections import OrderedDict
    people: OrderedDict[str, dict] = OrderedDict()
    for r in rows:
        pid = str(r["personnel_id"])
        if pid not in people:
            people[pid] = {
                "name": r["personnel_name"],
                "skills": r["skills"],
                "assignments": [],
            }
        if r["project_id"] is not None:
            people[pid]["assignments"].append({
                "project_id": str(r["project_id"]),
                "project_name": r["project_name"],
                "start_date": str(r["start_date"]),
                "end_date": str(r["end_date"]),
                "sequence": r["sequence"],
                "assignment_type": r["assignment_type"],
            })

    # Build personnel text with available windows
    lines = ["PERSONNEL & AVAILABILITY:"]
    for pid, info in people.items():
        lines.append(f"\n{info['name']} (id:{pid}), skills: [{info['skills']}]")
        assignments = sorted(info["assignments"], key=lambda a: a["start_date"])
        if assignments:
            lines.append("  Current assignments:")
            for a in assignments:
                lines.append(
                    f"    seq {a['sequence']}: {a['project_name']} "
                    f"({a['start_date']} to {a['end_date']}, {a['assignment_type']})"
                )
            # Compute available windows (gaps between assignments)
            windows = []
            for i in range(len(assignments) - 1):
                gap_start = assignments[i]["end_date"]
                gap_end = assignments[i + 1]["start_date"]
                if gap_start < gap_end:
                    windows.append(f"    {gap_start} to {gap_end} (gap)")
            # Open window after last assignment
            last_end = assignments[-1]["end_date"]
            windows.append(f"    {last_end} onward (open)")
            lines.append("  Available windows:")
            lines.extend(windows)
        else:
            lines.append("  No current assignments — fully available")

    # Build unscheduled projects text
    lines.append("\n\nUNSCHEDULED PROJECTS:")
    if unscheduled:
        for p in unscheduled:
            lines.append(
                f"- {p['name']} (id:{p['id']}): requires [{p['required_skills']}], "
                f"{p['num_elevators']} elevators, "
                f"contract {p['contract_start_date']} to {p['contract_end_date']}, "
                f"{p['duration_weeks']} weeks"
            )
    else:
        lines.append("(none)")

    return "\n".join(lines)


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
    contract_end_date: Optional[str] = None
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


class CascadeEndDateRequest(BaseModel):
    new_end_date: str
    scenario_id: str


class ShiftScheduleRequest(BaseModel):
    new_start_date: str


class ScenarioCreate(BaseModel):
    name: str


class ChatRequest(BaseModel):
    messages: list[dict]


class HomeAssessmentRequest(BaseModel):
    upcoming: list[dict]
    project_stats: dict
    personnel_stats: dict


# ── Home ──────────────────────────────────────────────────────────────────────

@router.get("/api/home/stats")
async def get_home_stats(scenario_id: Optional[str] = None):
    sid = _get_scenario_id(scenario_id)
    if not sid:
        return {"upcoming": [], "project_stats": {}, "personnel_stats": {}}
    return {
        "upcoming": fetch_home_upcoming(sid),
        "project_stats": fetch_home_project_stats(sid),
        "personnel_stats": fetch_home_personnel_stats(sid),
    }


@router.post("/api/home/assessment")
async def get_home_assessment(data: HomeAssessmentRequest):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    system_prompt = f"""You are a scheduling health analyst for an elevator installation company.
Today's date: {today}

You will receive JSON with three fields:
- "upcoming": each mechanic's current active assignment and their next assignment (by sequence). event_type is "active" (ongoing now), "upcoming" (starts in the future), or "ending_soon" (ends within 14 days).
- "project_stats": awarded project counts — total, staffed (has >=1 assignment), unstaffed, and staffed percentage.
- "personnel_stats": roster counts — total, currently_assigned (active today), has_future_assignment, and unassigned.

Provide a balanced project health summary in 3-6 bullet points. Lead with what's going well, then note areas needing attention. Only flag something as urgent if it is genuinely time-sensitive. Do not speculate about data or system issues — treat the data as accurate. Be concise and direct. Do not use emoji."""
    user_msg = json.dumps({
        "upcoming": data.upcoming,
        "project_stats": data.project_stats,
        "personnel_stats": data.personnel_stats,
    }, default=str)
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "\n".join(b.text for b in response.content if b.type == "text")
    return {"assessment": text}


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
    # Recalculate dates based on what was provided
    if "contract_end_date" in updates and "duration_weeks" not in updates and "contract_start_date" not in updates:
        # End date provided alone — calculate duration from it
        current = fetch_project_by_id(project_id)
        if not current:
            raise HTTPException(404, "Project not found")
        start = datetime.strptime(str(current["contract_start_date"]), "%Y-%m-%d")
        end = datetime.strptime(updates["contract_end_date"], "%Y-%m-%d")
        updates["duration_weeks"] = max(1, (end - start).days + 6) // 7
    elif "contract_start_date" in updates or "duration_weeks" in updates:
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


@router.post("/api/assignments/{assignment_id}/cascade")
async def cascade_end_date(assignment_id: str, data: CascadeEndDateRequest):
    result = cascade_assignment_end_date(data.scenario_id, assignment_id, data.new_end_date)
    if not result["updated"]:
        raise HTTPException(status_code=404, detail="Assignment not found")
    # Check if any shifted assignment's end_date exceeds its project's contract_end_date
    all_affected = [result["updated"]] + result["shifted"]
    for assign in all_affected:
        project = fetch_project_by_id(str(assign["project_id"]))
        if project and str(assign["end_date"]) > str(project["contract_end_date"]):
            new_end = assign["end_date"]
            start = project["contract_start_date"]
            delta_days = (new_end - start).days
            new_weeks = (delta_days + 6) // 7  # round up
            update_project(str(project["id"]), {
                "contract_end_date": str(new_end),
                "duration_weeks": new_weeks,
            })
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
            detail="A draft already exists. Delete or promote it first."
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
        # Archive old master's assignments, then hard-delete the scenario row
        archive_scenario_assignments(master["id"], master["name"])
        db_delete_scenario(master["id"])
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


# ── Archive ────────────────────────────────────────────────────────────────────

@router.get("/api/archive/scenarios")
async def get_archived_scenarios():
    return fetch_archived_scenarios()


@router.get("/api/archive/assignments")
async def get_archived_assignments(scenario_id: str):
    return fetch_archived_assignments(scenario_id)


# ── Chat ───────────────────────────────────────────────────────────────────────

@router.post("/api/chat")
async def chat(request: ChatRequest):
    master = fetch_master_scenario()

    # Draft-aware context: if a draft exists, use it so Claude sees current draft state
    is_tweaking = False
    active_drafts = fetch_active_drafts()
    if active_drafts:
        draft = active_drafts[0]
        sid = draft["id"]
        is_tweaking = True
    elif master:
        sid = master["id"]
    else:
        sid = None

    # Build pre-computed context string
    ai_context = _build_ai_context(sid) if sid else "No scenario data available."

    system_prompt = f"""You are a helpful scheduling assistant for an elevator installation company.
You have real-time access to the following data from the database:

{ai_context}

Answer questions about projects, scheduling, resource allocation, and team assignments based on this data.
When asked about a personnel member's next project, look up their assignments directly.
Today's date is {now_iso()}.

Keep responses concise. Use short bullet points, not tables. When summarizing a schedule, use simple lines like: 'John Smith → Project Alpha (Jan 6 – Mar 30)'. Only use markdown tables if the user explicitly requests one.

Avoid using emojis unless they convey unambiguous meaning in context.

If I tell you to give me a recommendation for how to schedule a bunch of projects, just give me a simple output via:
Mechanic Name (Available Date) --> Project Name (Contract Start Date).
Make sure to ask if I want to match skills or not.

SCHEDULE GENERATION INSTRUCTIONS:
You have a tool called "generate_schedule" that creates a draft schedule in the system.
Only use this tool when the user EXPLICITLY asks you to CREATE, GENERATE, or BUILD a schedule.
Do NOT use the tool for questions, recommendations, or analysis — only for actual schedule creation.

When generating a schedule:
- IMPORTANT: Only schedule projects listed under UNSCHEDULED PROJECTS above. Projects that already have assignments are preserved automatically — do NOT re-schedule them.
- Use the PERSONNEL & AVAILABILITY section above to find available windows. Do not create overlapping date ranges for the same person.
- Match personnel skills to project required_skills. If a person's skills overlap with the project's required skills, they are a candidate.
- CRITICAL DATE RULE: end_date = start_date + duration_weeks. This is the ONLY way to compute end_date.
  - contract_start_date is the EARLIEST a project can start. If a mechanic is not available until later, the project starts later.
  - contract_end_date is informational only — NEVER use it as an assignment end_date.
  - If a mechanic is unavailable until after contract_start_date, set start_date = mechanic's available date, and end_date = start_date + duration_weeks.
- Number NEW assignments sequentially per person, continuing from their highest existing sequence number.
- Default assignment_type to "full".
- Only schedule projects with award_status = 'awarded' unless the user explicitly asks otherwise.
- Give the draft a descriptive name reflecting the strategy used.
- Before calling the tool, briefly explain your scheduling strategy to the user.
- After the tool executes, summarize what was created (how many assignments, which personnel/projects).
"""

    # Add tweak-mode instructions when a draft exists
    if is_tweaking:
        system_prompt += """
TWEAK MODE — ACTIVE DRAFT:
You are viewing an existing draft schedule, not the master. The user wants to make changes to this draft.
- Apply the user's requested changes to the current assignment set.
- When you call generate_schedule, output the FULL set of assignments for ALL previously-unscheduled projects (both changed and unchanged ones).
- The system will automatically delete the old draft and create a new one with your assignments.
- Master assignments (already scheduled projects) are copied automatically — do NOT include them in your output.
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
    tool_result = _execute_schedule_tool(tool_use_block.input, is_tweaking=is_tweaking)

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
