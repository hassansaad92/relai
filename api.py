from dotenv import load_dotenv
load_dotenv()

import math
import os
from datetime import date, datetime, timedelta, timezone
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
    fetch_all_awarded_projects,
    insert_chat_log,
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
    delete_movable_assignments,
)

router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

MAX_ACTIVE_DRAFTS = 1

logger = logging.getLogger(__name__)

def compute_duration_days(man_hours: float | None, crew_hours: float | None, allow_overtime: bool = False) -> float:
    """Compute duration_days from man_hours + crew_hours using half-day rounding.

    Standard (8h day): ceil(total/4) * 0.5  →  e.g. 3h=0.5d, 5h=1d, 9h=1.5d
    Overtime (12h day): ceil(total/6) * 0.5  →  e.g. 7h=1d, 13h=1.5d
    """
    mh = man_hours or 0
    ch = crew_hours or 0
    total = mh + ch
    if total <= 0:
        return 0
    divisor = 6 if allow_overtime else 4
    return math.ceil(total / divisor) * 0.5


def add_business_days(start: date, days: int) -> date:
    """Add N business days (Mon-Fri) to a start date. days=0 returns start itself."""
    if days <= 0:
        return start
    current = start
    remaining = days
    while remaining > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Mon-Fri
            remaining -= 1
    return current


def count_business_days(start: date, end: date) -> int:
    """Count business days between start and end (inclusive of both)."""
    if end < start:
        return 0
    count = 0
    current = start
    while current <= end:
        if current.weekday() < 5:
            count += 1
        current += timedelta(days=1)
    return count


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
                        "allocated_days": {
                            "type": "number",
                            "description": "Daily allocation: 1.0 for full day, 0.5 for half day. Default 1.0.",
                            "default": 1.0,
                        },
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

        # Remove future/movable assignments — AI will replace them
        today_str = date.today().isoformat()
        delete_movable_assignments(scenario_id, today_str)

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
                "work_mode": r.get("work_mode", "crew"),
                "assignments": [],
            }
        if r["project_id"] is not None:
            people[pid]["assignments"].append({
                "project_id": str(r["project_id"]),
                "project_name": r["project_name"],
                "start_date": str(r["start_date"]),
                "end_date": str(r["end_date"]),
                "sequence": r["sequence"],
                "allocated_days": float(r["allocated_days"]) if r.get("allocated_days") is not None else 1.0,
                "assignment_type": r["assignment_type"],
                "committed_start": str(r["committed_start_date"]) if r.get("committed_start_date") else None,
                "committed_end": str(r["committed_end_date"]) if r.get("committed_end_date") else None,
                "duration_days": float(r["duration_days"]) if r.get("duration_days") is not None else None,
            })

    # Build personnel text with available windows
    today_str = date.today().isoformat()
    lines = ["PERSONNEL & AVAILABILITY:"]
    for pid, info in people.items():
        lines.append(f"\n{info['name']} (id:{pid}), skills: [{info['skills']}], work_mode: {info['work_mode']}")
        assignments = sorted(info["assignments"], key=lambda a: a["start_date"])
        if assignments:
            lines.append("  Current assignments:")
            for a in assignments:
                lock_label = "[LOCKED]" if a['start_date'] <= today_str else "[MOVABLE]"
                alloc_label = f", {a['allocated_days']} days/day" if a['allocated_days'] != 1.0 else ""
                committed_label = ""
                if a.get('committed_start') or a.get('committed_end'):
                    committed_label = f", committed: {a.get('committed_start', '?')} to {a.get('committed_end', '?')}"
                lines.append(
                    f"    {lock_label} seq {a['sequence']}: {a['project_name']} "
                    f"({a['start_date']} to {a['end_date']}, {a['assignment_type']}{alloc_label}{committed_label})"
                )
            # Compute available windows (gaps between assignments)
            windows = []
            for i in range(len(assignments) - 1):
                gap_start_dt = datetime.strptime(assignments[i]["end_date"], "%Y-%m-%d") + timedelta(days=1)
                gap_end = assignments[i + 1]["start_date"]
                if gap_start_dt.strftime("%Y-%m-%d") < gap_end:
                    windows.append(f"    {gap_start_dt.strftime('%Y-%m-%d')} to {gap_end} (gap)")
            # Open window after last assignment
            last_end_dt = datetime.strptime(assignments[-1]["end_date"], "%Y-%m-%d") + timedelta(days=1)
            windows.append(f"    {last_end_dt.strftime('%Y-%m-%d')} onward (open)")
            lines.append("  Available windows:")
            lines.extend(windows)
        else:
            lines.append("  No current assignments — fully available")

    # Build all-projects reference for name→ID lookup
    all_projects = fetch_all_awarded_projects()
    lines.append("\n\nALL PROJECTS (reference):")
    if all_projects:
        for p in all_projects:
            lines.append(f"- {p['name']} (id:{p['id']})")
    else:
        lines.append("(none)")

    # Build unscheduled projects text
    lines.append("\n\nUNSCHEDULED PROJECTS:")
    if unscheduled:
        for p in unscheduled:
            procurement = f", procurement: {p['procurement_date']}" if p.get('procurement_date') else ""
            ot_flag = ", allow_overtime=true" if p.get('allow_overtime') else ""
            acct = f", account_type={p['account_type']}" if p.get('account_type') and p['account_type'] != 'standard' else ""
            cust = f", customer_id={p['customer_id']}" if p.get('customer_id') else ""
            hours_info = ""
            if p.get('man_hours') or p.get('crew_hours'):
                mh = float(p['man_hours']) if p.get('man_hours') else 0
                ch = float(p['crew_hours']) if p.get('crew_hours') else 0
                hours_info = f", man_hours={mh}, crew_hours={ch}"
            material_info = ""
            if p.get('material_arrived') is not None:
                material_info = f", material_arrived={'yes' if p['material_arrived'] else 'no'}"
                if not p['material_arrived'] and p.get('procurement_date'):
                    material_info += f" (expected: {p['procurement_date']})"
            wo_info = f", WO#={p['work_order_number']}" if p.get('work_order_number') else ""
            div_info = f", division={p['division']}" if p.get('division') else ""
            equip_info = f", equipment={p['equipment']}" if p.get('equipment') else ""
            lines.append(
                f"- {p['name']} (id:{p['id']}): requires [{p['required_skills']}], "
                f"contract {p['committed_start_date']} to {p['committed_end_date']}, "
                f"{p['duration_days']} days{hours_info}{procurement}{ot_flag}{material_info}{acct}{cust}{wo_info}{div_info}{equip_info}"
            )
    else:
        lines.append("(none)")

    lines.append("\n\nSCHEDULING CONSTRAINTS:")
    lines.append("- Standard day = 8 hours. Duration uses half-day rounding: ceil(hours/4) * 0.5 days.")
    lines.append("- If allow_overtime=true: day = 12 hours, formula is ceil(hours/6) * 0.5 days. Mechanics can work weekends but max 60 hours/week.")
    lines.append("- Projects with material_arrived=false should not be scheduled until their procurement_date.")
    lines.append("- Projects with zero hours (man_hours=0, crew_hours=0, duration_days=0) are excluded — they need hours entered first.")

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
    work_mode: str = "crew"


class PersonnelUpdate(BaseModel):
    name: Optional[str] = None
    skills: Optional[str] = None
    work_mode: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    required_skills: str
    committed_start_date: Optional[str] = None
    duration_days: Optional[float] = None
    award_status: str
    procurement_date: Optional[str] = None
    allow_overtime: bool = False
    customer_id: Optional[str] = None
    account_type: str = "standard"
    work_order_number: Optional[str] = None
    work_order_date: Optional[str] = None
    equipment: Optional[str] = None
    material_status: Optional[str] = None
    material_arrived: Optional[bool] = None
    division: Optional[str] = None
    sales_rep: Optional[str] = None
    description: Optional[str] = None
    man_hours: Optional[float] = None
    crew_hours: Optional[float] = None
    total_amount: Optional[float] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    required_skills: Optional[str] = None
    committed_start_date: Optional[str] = None
    committed_end_date: Optional[str] = None
    duration_days: Optional[float] = None
    award_status: Optional[str] = None
    procurement_date: Optional[str] = None
    allow_overtime: Optional[bool] = None
    customer_id: Optional[str] = None
    account_type: Optional[str] = None
    work_order_number: Optional[str] = None
    work_order_date: Optional[str] = None
    equipment: Optional[str] = None
    material_status: Optional[str] = None
    material_arrived: Optional[bool] = None
    division: Optional[str] = None
    sales_rep: Optional[str] = None
    description: Optional[str] = None
    man_hours: Optional[float] = None
    crew_hours: Optional[float] = None
    total_amount: Optional[float] = None


class SkillCreate(BaseModel):
    skill: str


class AssignmentCreate(BaseModel):
    personnel_id: str
    project_id: str
    scenario_id: str
    sequence: int
    start_date: str
    end_date: str
    allocated_days: float = 1.0
    assignment_type: str = "full"


class AssignmentUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    allocated_days: Optional[float] = None
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
    # Compute duration_days from hours if not explicitly provided
    if data.get("duration_days") is None:
        data["duration_days"] = compute_duration_days(data.get("man_hours"), data.get("crew_hours"), data.get("allow_overtime", False))
    if data.get("committed_start_date"):
        start_dt = datetime.strptime(data["committed_start_date"], "%Y-%m-%d").date()
        days = math.ceil(data["duration_days"])
        if days <= 0:
            data["committed_end_date"] = start_dt.isoformat()
        elif data.get("allow_overtime"):
            end_dt = start_dt + timedelta(days=days - 1)
            data["committed_end_date"] = end_dt.isoformat()
        else:
            end_dt = add_business_days(start_dt, days - 1)
            data["committed_end_date"] = end_dt.isoformat()
    else:
        data["committed_start_date"] = None
        data["committed_end_date"] = None
    if not data.get("procurement_date"):
        data["procurement_date"] = None
    if not data.get("customer_id"):
        data["customer_id"] = None
    # Set None defaults for new nullable fields
    for field in ("work_order_number", "work_order_date", "equipment", "material_status",
                  "material_arrived", "division", "sales_rep", "description", "man_hours", "crew_hours", "total_amount"):
        if not data.get(field):
            data[field] = None
    return insert_project(data)


@router.delete("/api/projects/{project_id}")
async def remove_project(project_id: str):
    delete_assignments_by_project(project_id)
    delete_project(project_id)
    return {"success": True}


@router.patch("/api/projects/{project_id}")
async def patch_project(project_id: str, data: ProjectUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    # Allow explicitly setting procurement_date to empty string (clear it)
    if data.procurement_date is not None:
        updates["procurement_date"] = data.procurement_date if data.procurement_date else None
    # Allow explicitly setting material_arrived to false
    if data.material_arrived is not None:
        updates["material_arrived"] = data.material_arrived
    if not updates:
        raise HTTPException(400, "No fields to update")
    # Fetch current project once for recalculations
    current = fetch_project_by_id(project_id)
    if not current:
        raise HTTPException(404, "Project not found")
    # Determine allow_overtime: use the update value if provided, else use current
    ot = updates.get("allow_overtime")
    if ot is None:
        ot = current.get("allow_overtime", False)
    # Recompute duration_days when hours change
    if "man_hours" in updates or "crew_hours" in updates:
        mh = updates.get("man_hours") if "man_hours" in updates else (float(current["man_hours"]) if current.get("man_hours") else None)
        ch = updates.get("crew_hours") if "crew_hours" in updates else (float(current["crew_hours"]) if current.get("crew_hours") else None)
        if mh is not None or ch is not None:
            updates["duration_days"] = compute_duration_days(mh, ch, ot)
    # Recalculate committed dates based on what was provided
    if "committed_end_date" in updates and "duration_days" not in updates and "committed_start_date" not in updates:
        # End date provided alone — calculate duration from it
        if current["committed_start_date"]:
            start_dt = date.fromisoformat(str(current["committed_start_date"]))
            end_dt = date.fromisoformat(updates["committed_end_date"])
            if ot:
                updates["duration_days"] = max(1, (end_dt - start_dt).days + 1)
            else:
                updates["duration_days"] = max(1, count_business_days(start_dt, end_dt))
    elif "committed_start_date" in updates or "duration_days" in updates:
        start_str = updates.get("committed_start_date")
        days = updates.get("duration_days")
        start_str = start_str or (str(current["committed_start_date"]) if current["committed_start_date"] else None)
        days = days or float(current["duration_days"])
        if start_str and days:
            start_dt = date.fromisoformat(start_str)
            if ot:
                updates["committed_end_date"] = (start_dt + timedelta(days=math.ceil(days) - 1)).isoformat()
            else:
                updates["committed_end_date"] = add_business_days(start_dt, math.ceil(days) - 1).isoformat()
    result = update_project(project_id, updates)
    if not result:
        raise HTTPException(404, "Project not found")
    return result


# ── Bulk Upload ────────────────────────────────────────────────────────────────

class ColumnMappingRequest(BaseModel):
    headers: list[str]
    sample_rows: list[dict]


class BulkProjectImportRequest(BaseModel):
    projects: list[dict]


COLUMN_MAPPING_TOOL = {
    "name": "map_columns",
    "description": "Map spreadsheet column names to project fields",
    "input_schema": {
        "type": "object",
        "properties": {
            "mappings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "column": {"type": "string", "description": "The original spreadsheet column name"},
                        "field": {
                            "type": ["string", "null"],
                            "enum": [
                                "name", "required_skills", "duration_days",
                                "committed_start_date", "committed_end_date",
                                "procurement_date", "award_status", "allow_overtime",
                                "customer_id", "account_type",
                                "work_order_number", "work_order_date", "equipment",
                                "material_status", "material_arrived", "division", "sales_rep",
                                "description", "man_hours", "crew_hours", "total_amount",
                                None
                            ],
                            "description": "The project field to map to, or null to skip"
                        }
                    },
                    "required": ["column", "field"]
                }
            }
        },
        "required": ["mappings"]
    }
}


@router.post("/api/projects/map-columns")
async def map_columns(data: ColumnMappingRequest):
    prompt = f"""Map these spreadsheet columns to project fields. CAREFULLY examine both the column names AND the sample data values to make correct mappings.

Project fields and their meaning:
- name: Building/project name (required)
- required_skills: Comma-separated skills needed (e.g. "Modernization,Construction")
- duration_days: Number of working days (numeric). Only use if the column is explicitly "days".
- man_hours: Individual mechanic hours (numeric). Map columns like "Man Hours", "Labor Hours", "Est Hours" here.
- crew_hours: Team/crew hours (numeric). Map columns like "Crew Hours", "Team Hours" here.
- committed_start_date: Start date — must be an actual DATE value (e.g. "2025-03-01", "3/1/2025")
- committed_end_date: End/completion date — must be an actual DATE value
- procurement_date: Material procurement DATE — must be an actual DATE value (e.g. "2025-04-15"). Do NOT map status/text columns here (e.g. "Ordered", "Pending", "Complete" are NOT dates).
- award_status: One of "awarded" or "prospect" — a text status field
- allow_overtime: Whether weekends are allowed (boolean)
- customer_id: Customer identifier
- account_type: "standard" or "priority"
- work_order_number: Work order / WO number (e.g. "WO-39911-F1F1")
- work_order_date: Date the work order was created — must be an actual DATE value
- equipment: Equipment identifier or type (e.g. "135429", "Elevator", "WCL Lift")
- material_status: Material/procurement status text (e.g. "Material Required", "Ordered", "Complete")
- material_arrived: Whether material has arrived (boolean)
- division: Business division (e.g. "Repair", "Install", "Modernization")
- sales_rep: Sales rep or owner name
- description: Work description / notes text
- total_amount: Dollar value / total amount (numeric)

IMPORTANT RULES:
- Look at the SAMPLE DATA to determine the actual data type. A column named "Procurement" with values like "Ordered" or "Complete" is a status — map to material_status, NOT procurement_date.
- Only map to date fields (committed_start_date, committed_end_date, procurement_date, work_order_date) if the sample values are actual dates.
- If a column contains hours, map to man_hours or crew_hours (not duration_days). The system auto-computes days from hours.
- Set field to null for columns that don't match any project field.

Spreadsheet columns: {json.dumps(data.headers)}
Sample data (first 2 rows): {json.dumps(data.sample_rows[:2])}

Map each column to the most appropriate field based on both the column name and the actual data values."""

    response = anthropic_client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        tools=[COLUMN_MAPPING_TOOL],
        tool_choice={"type": "tool", "name": "map_columns"},
    )

    for block in response.content:
        if block.type == "tool_use":
            return {"mappings": block.input.get("mappings", [])}

    return {"mappings": [{"column": h, "field": None} for h in data.headers]}


@router.post("/api/projects/bulk")
async def bulk_import_projects(data: BulkProjectImportRequest):
    imported = 0
    errors = []
    for i, proj in enumerate(data.projects):
        try:
            # Validate required fields
            if not proj.get("name"):
                errors.append({"row": i + 1, "message": "Missing project name"})
                continue

            # Parse hours
            man_hours_val = float(proj["man_hours"]) if proj.get("man_hours") else None
            crew_hours_val = float(proj["crew_hours"]) if proj.get("crew_hours") else None
            allow_ot = bool(proj.get("allow_overtime", False))
            # Compute duration_days: from hours if available, else from explicit duration_days, else default to 0
            if man_hours_val is not None or crew_hours_val is not None:
                duration_days_val = compute_duration_days(man_hours_val, crew_hours_val, allow_ot)
            elif proj.get("duration_days"):
                duration_days_val = float(proj["duration_days"])
            else:
                # No hours and no duration — import with zero (flagged on dashboard)
                man_hours_val = 0
                crew_hours_val = 0
                duration_days_val = 0

            # Build project data with defaults
            project_data = {
                "name": str(proj["name"]).strip(),
                "required_skills": str(proj.get("required_skills", "")).strip() or "General",
                "duration_days": duration_days_val,
                "award_status": str(proj.get("award_status", "awarded")).strip().lower(),
                "allow_overtime": bool(proj.get("allow_overtime", False)),
                "customer_id": proj.get("customer_id") or None,
                "account_type": str(proj.get("account_type", "standard")).strip().lower(),
                "committed_start_date": None,
                "committed_end_date": None,
                "procurement_date": None,
                "work_order_number": proj.get("work_order_number") or None,
                "work_order_date": proj.get("work_order_date") or None,
                "equipment": proj.get("equipment") or None,
                "material_status": proj.get("material_status") or None,
                "material_arrived": bool(proj["material_arrived"]) if proj.get("material_arrived") is not None and str(proj.get("material_arrived", "")).strip() != "" else None,
                "division": proj.get("division") or None,
                "sales_rep": proj.get("sales_rep") or None,
                "description": proj.get("description") or None,
                "man_hours": man_hours_val,
                "crew_hours": crew_hours_val,
                "total_amount": float(proj["total_amount"]) if proj.get("total_amount") else None,
            }

            # Validate award_status
            if project_data["award_status"] not in ("awarded", "prospect"):
                project_data["award_status"] = "awarded"

            # Validate account_type
            if project_data["account_type"] not in ("standard", "priority"):
                project_data["account_type"] = "standard"

            # Calculate committed dates
            start_str = proj.get("committed_start_date")
            end_str = proj.get("committed_end_date")
            if start_str:
                start_dt = datetime.strptime(str(start_str).strip(), "%Y-%m-%d").date()
                project_data["committed_start_date"] = start_dt.isoformat()
                days = math.ceil(project_data["duration_days"])
                if project_data["allow_overtime"]:
                    end_dt = start_dt + timedelta(days=days - 1)
                else:
                    end_dt = add_business_days(start_dt, days - 1)
                project_data["committed_end_date"] = end_dt.isoformat()
            elif end_str:
                # If only end date provided, store it but no start
                project_data["committed_end_date"] = str(end_str).strip()

            # Procurement date
            proc_str = proj.get("procurement_date")
            if proc_str:
                project_data["procurement_date"] = str(proc_str).strip()

            insert_project(project_data)
            imported += 1
        except Exception as e:
            errors.append({"row": i + 1, "message": str(e)})

    return {"imported": imported, "errors": errors}


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

    # Log user prompt (fire-and-forget)
    try:
        user_messages = [m for m in request.messages if m.get("role") == "user"]
        if user_messages:
            last_user_msg = user_messages[-1].get("content", "")
            insert_chat_log({
                "user_prompt": last_user_msg,
                "scenario_id": sid,
                "is_tweaking": is_tweaking,
            })
    except Exception:
        logger.debug("Failed to log chat prompt", exc_info=True)

    # Build pre-computed context string
    ai_context = _build_ai_context(sid) if sid else "No scenario data available."

    system_prompt = f"""You are a helpful scheduling assistant for an elevator installation company.
You have real-time access to the following data from the database:

{ai_context}

Answer questions about projects, scheduling, resource allocation, and team assignments based on this data.
When asked about a personnel member's next project, look up their assignments directly.
Today's date is {now_iso()}.

HOURS MODEL: Projects may have man_hours (individual mechanic work) and crew_hours (team work). duration_days is computed as ceil((man_hours + crew_hours) / 8). Crew work happens first, then individual adjustments follow. Personnel have a work_mode (crew or individual) indicating whether they work in teams or solo.

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
- CRITICAL DATE RULE: By default, dates skip weekends (Sat/Sun). end_date = start_date + business_days(duration_days - 1). A 10-day project starting Mon 3/23 ends Fri 4/3 (skipping 2 weekends). If a project has allow_overtime=true, use calendar days instead (end_date = start_date + duration_days - 1).
  - committed_start_date is the EARLIEST a project can start. If a mechanic is not available until later, the project starts later.
  - committed_end_date is informational only — NEVER use it as an assignment end_date.
  - If a mechanic is unavailable until after committed_start_date, set start_date = mechanic's available date, and end_date = start_date + business_days(duration_days - 1) (or calendar days if allow_overtime=true).
- Number NEW assignments sequentially per person, continuing from their highest existing sequence number.
- Default assignment_type to "full" and allocated_days to 1.0.
- HALF-DAY ASSIGNMENTS: Set allocated_days based on the project's duration_days — if duration_days <= 0.5 use allocated_days = 0.5, otherwise use 1.0. Two half-day assignments (0.5 each) can share the same person on the same day without conflict. Total allocated_days per person per day must not exceed 1.0.
- PROCUREMENT DATE: Some projects have a procurement_date. Materials must be procured by this date. Factor this into scheduling — ideally start the project on or after the procurement date unless the user says otherwise.
- Only schedule projects with award_status = 'awarded' unless the user explicitly asks otherwise.
- Give the draft a descriptive name reflecting the strategy used.
- Before calling the tool, briefly explain your scheduling strategy to the user.
- After the tool executes, summarize what was created (how many assignments, which personnel/projects).

INCREMENTAL SCHEDULING:
Assignments are labeled [LOCKED] or [MOVABLE]:
- [LOCKED]: start_date <= today. These assignments are in progress or already started. NEVER move, modify, or re-output them.
- [MOVABLE]: start_date > today. These are future assignments that CAN be reshuffled to make room for new projects.
When scheduling new projects, you may rearrange [MOVABLE] assignments to fit the new work. The system will automatically remove all movable assignments from the draft and replace them with your output.
Only output assignments for [MOVABLE] slots and new projects — locked assignments are preserved automatically.

PRIORITY ACCOUNT SCHEDULING:
Projects with account_type='priority' are high-value accounts. When scheduling:
- Priority projects get the earliest available slots and the best skill-matched crew.
- If there is a conflict between a priority and a standard project for the same time slot, the priority project wins.
- Schedule all priority projects first, then fill remaining slots with standard projects.
"""

    # Add tweak-mode instructions when a draft exists
    if is_tweaking:
        system_prompt += """
TWEAK MODE — ACTIVE DRAFT:
You are viewing an existing draft schedule, not the master. The user wants to make changes to this draft.
- Apply the user's requested changes to the current assignment set.
- When you call generate_schedule, output the FULL set of MOVABLE assignments (both changed and unchanged ones). Do NOT include [LOCKED] assignments.
- The system will automatically delete the old draft, copy master assignments, preserve locked assignments, and layer your movable assignments on top.
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
