# Resource Planner — Product Specification

**Product Name:** RelAI
**Author:** Product Owner
**Version:** 0.1 — Initial Spec
**Last Updated:** March 2026

---

## 1. Problem Statement

At Otis Elevator Company, field operations teams managed roughly 100 mechanics and ~200 concurrent projects. Assignment scheduling was done manually — via spreadsheets, whiteboards, or institutional knowledge — with no single unified view of who was assigned where, what was coming up next, or how to quickly re-optimize when constraints changed. These were projects on the scale of 6 months in duration, and the planning was done manually every 2 weeks, during which we would shuffle a Gantt chart around by hand. 

This led to:
- Scheduling conflicts and under-utilization of mechanics
- Poor visibility into upcoming project staffing gaps
- No easy mechanism for planners to model "what-if" scenarios
- High cognitive load and suboptimal planning since the ops leads were managing all variables at once

---

## 2. Vision

A web-based **LLM-powered resource planning tool** that gives operations planners a real-time, unified view of mechanic assignments and project staffing — and allows them to adjust the schedule using either a traditional UI or natural language commands.

The LLM acts as a scheduling engine and conversational interface: it understands constraints, reasons about trade-offs, and adjusts assignments in response to planner instructions.

---

## 3. Users

**Primary user:** Operations Planner 
- Needs a bird's-eye view of all mechanics and all active/upcoming projects
- Makes scheduling decisions daily, weekly, and in response to changes
- Comfortable with both UI-driven interactions and typing natural language

**Secondary user (future):** Field Supervisor / Manager
- Read-only or limited-edit view
- Interested in reporting, coverage gaps, and forecasting

---

## 4. Core Concepts

| Concept | Definition |
|---|---|
| **Mechanic** | A field technician with a name, availability status, skill set, and location |
| **Project** | A job or work order with a start date, expected duration, required skills, and location |
| **Assignment** | A pairing of one mechanic to one project for a defined time period |
| **Current Assignment** | The project a mechanic is actively working on right now |
| **Next Assignment** | The next project queued for a mechanic (one look-ahead only in v1) |
| **Staffing Status** | Whether a project currently has a mechanic assigned (Staffed / Unstaffed) |
| **Schedule** | The full set of assignments across all mechanics and projects |

---

## 5. Functional Requirements

### 5.1 Dashboard View (v1)

The main screen displays two primary panels side-by-side (or stacked on mobile):

**Mechanics Panel**
- Lists all mechanics (name, status, current assignment, next assignment)
- Status indicator per mechanic: Available, On Job, Unavailable
- Each row shows:
  - Mechanic name
  - Current project (or "Unassigned")
  - Next project (or "None scheduled")
  - Quick action: manually reassign via dropdown or drag-and-drop

**Projects Panel**
- Lists all projects
- Each row shows:
  - Project name / ID
  - Start date and expected end date
  - Required skills / role
  - Location
  - Staffing status: Staffed (green) / Unstaffed (red)
  - Assigned mechanic(s), if any

Both panels support:
- Text search / filter by name, status, or date
- Sort by column headers
- Color-coded status indicators

### 5.2 Assignment Workflow (v1)

Planners can manually create or change assignments via the UI:
- Click a project → assign a mechanic from a dropdown of available mechanics
- Click a mechanic → assign them to a project from a dropdown of unstaffed projects
- Drag-and-drop mechanic onto a project row (stretch goal for v1)

When an assignment changes:
- The schedule updates in real-time
- Conflict warnings surface if the mechanic is already assigned in the same time window
- The LLM can optionally suggest an alternative if a conflict is detected

### 5.3 LLM Scheduling Engine (v1)

The LLM is the core scheduling brain. It is invoked:
1. On initial load, to compute an optimized baseline schedule from all mechanics + projects
2. When the planner issues a natural language command via the Chat Window
3. When a manual UI change creates a conflict (LLM suggests a resolution)

The LLM receives a full context payload on each invocation:
```
- List of all mechanics (name, skills, availability, location, current and next assignments)
- List of all projects (ID, name, dates, required skills, location, staffing status)
- Current full assignment schedule
- The planner's instruction or change request
```

The LLM returns:
```
- Updated assignment schedule (structured JSON)
- A plain-English explanation of what changed and why
- Any warnings (e.g., "No mechanics with skill X are available for Project Y in this window")
```

### 5.4 Chat Window (v1 — core feature)

A persistent chat panel (side drawer or bottom panel) where the planner types natural language instructions.

Example prompts the system must handle:

| Prompt | Expected Behavior |
|---|---|
| "Put John Smith on Project Alpha starting in 10 months" | Schedules John Smith on Project Alpha at that future date; adjusts his current next assignment if needed; flags conflicts |
| "Who is available in March?" | Returns a list of mechanics with no current assignment in March |
| "Unstaffed projects this week?" | Returns all projects in the current week with no mechanic assigned |
| "Reassign everyone from Project Beta — it's been cancelled" | Frees all mechanics on Project Beta; marks them available; suggests re-assignments |
| "Find someone with elevator hydraulics experience for Project Gamma" | Filters mechanics by skill and recommends the best available match |
| "What would happen if we moved Sarah to Chicago next month?" | Runs a what-if scenario without committing changes; shows the downstream impact |

The Chat Window shows:
- The planner's message (right-aligned)
- The LLM's response including what changed (left-aligned)
- A diff/summary of schedule changes resulting from the command
- A "Confirm" and "Cancel" button before any changes are committed to the schedule

### 5.5 What-If / Scenario Mode (v1 stretch / v2)

Planners can enter a "draft mode" where:
- Instructions are applied to a copy of the current schedule, not the live schedule
- The planner can see the proposed schedule side-by-side with the current one
- On confirmation, the draft is promoted to the live schedule
- On discard, the draft is thrown away

This enables low-risk exploration of scheduling changes.

---

## 6. Data Model

```
Mechanic {
  id: string
  name: string
  skills: string[]
  homeLocation: string
  availability: "available" | "on_job" | "unavailable"
  currentAssignment: AssignmentID | null
  nextAssignment: AssignmentID | null
}

Project {
  id: string
  name: string
  startDate: date
  endDate: date
  location: string
  requiredSkills: string[]
  staffingStatus: "staffed" | "unstaffed"
  assignedMechanicIds: string[]
}

Assignment {
  id: string
  mechanicId: string
  projectId: string
  startDate: date
  endDate: date
  status: "current" | "upcoming" | "completed"
}

ScheduleSnapshot {
  createdAt: timestamp
  assignments: Assignment[]
  generatedBy: "llm" | "manual"
  notes: string
}
```

---

## 7. LLM Integration Design

### 7.1 Model

Use Claude (claude-sonnet-4-20250514) via the Anthropic API.

### 7.2 System Prompt Strategy

The LLM is given a system prompt establishing its role:

```
You are a resource scheduling assistant for a field operations team. 
You manage assignments between mechanics and projects. 
You respond to planner instructions and return updated schedules as structured JSON,
along with a plain-English explanation of every change made.
Always flag conflicts, skill mismatches, or coverage gaps.
When asked for what-if scenarios, clearly label the response as hypothetical.
```

### 7.3 Context Window Management

On each LLM call, include:
- Full mechanic list (compact JSON)
- Full project list (compact JSON)
- Current assignment schedule (compact JSON)
- Last N messages from the chat history (for conversation continuity)
- The new planner instruction

At ~100 mechanics and ~200 projects, the full context is well within Claude's context window. Re-send the full state on each request rather than attempting differential updates (simpler and more reliable at this scale).

### 7.4 Structured Output

Prompt the LLM to return a JSON block inside its response:

```json
{
  "scheduleChanges": [
    {
      "action": "assign" | "unassign" | "reassign",
      "mechanicId": "...",
      "projectId": "...",
      "startDate": "...",
      "endDate": "...",
      "reason": "..."
    }
  ],
  "warnings": ["..."],
  "summary": "Plain-English explanation of all changes"
}
```

The frontend parses this JSON to update the UI; the plain-English summary is displayed in the chat window.

---

## 8. Technical Architecture

```
Frontend (React)
  ├── Dashboard View
  │     ├── Mechanics Panel
  │     └── Projects Panel
  ├── Chat Window (drawer/panel)
  └── Scenario Mode (draft overlay)

Backend (Node.js / Express or Next.js API routes)
  ├── /api/schedule     — GET current schedule, POST updated schedule
  ├── /api/mechanics    — CRUD for mechanics
  ├── /api/projects     — CRUD for projects
  └── /api/chat         — Proxy to Anthropic API with context injection

Database (PostgreSQL or SQLite for MVP)
  ├── mechanics
  ├── projects
  ├── assignments
  └── schedule_snapshots (audit trail)

LLM
  └── Anthropic Claude API (claude-sonnet-4-20250514)
```

For MVP, a lightweight setup is preferred: Next.js (frontend + API routes in one), PostgreSQL or SQLite, and the Anthropic SDK.

---

## 9. UX / UI Guidelines

- **Color coding:** Green = staffed / available. Red = unstaffed / unavailable. Yellow = conflict / warning.
- **Density:** The dashboard must be scannable at a glance for ~100 mechanics and ~200 projects. Default to a compact table view with expandable rows for details.
- **Responsiveness:** Desktop-first. Mobile is not a priority for v1 but the layout should not break.
- **Confirmation gates:** All LLM-driven changes require the planner to explicitly confirm before the schedule is updated. No auto-commit.
- **Undo:** Maintain a schedule history so any committed change can be rolled back one step.

---

## 10. Out of Scope (v1)

- Multi-user / real-time collaborative editing
- Mobile app
- Integration with external ERP or workforce management systems (e.g., SAP, Workday)
- Automatic notifications or push alerts to mechanics
- Multi-step future scheduling (v1 shows only current + next assignment per mechanic)
- Reporting, dashboards, or analytics views
- Role-based access control (all users have full access in v1)

---

## 11. Phased Roadmap

| Phase | Scope |
|---|---|
| **v1 MVP** | Dashboard (mechanics + projects panels), manual assignment UI, LLM chat window, confirm/cancel gate, basic CRUD for mechanics and projects |
| **v2** | Scenario / what-if mode, schedule history + undo, skill-based filtering, conflict detection improvements |
| **v3** | Multi-user support, notifications, reporting, external integrations |

---

## 12. Open Questions

1. How is mechanic availability currently tracked? Is there an existing system to import from, or will it be manually entered?
2. Are there skills/certifications that need to be modeled, or is it sufficient to match by mechanic name and general availability?
3. What is the source of truth for project data — manual entry in this tool, or imported from a work order system?
4. Should the schedule distinguish between full-time assignment and partial allocation (e.g., a mechanic splitting time between two projects)?
5. Is there a concept of project priority that the LLM should factor into scheduling decisions?
6. What does "unavailable" mean in practice — PTO, training, out sick? Does the granularity matter?