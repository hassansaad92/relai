# In-App Claude: Assignment Manipulation

## Context

The app already has a chat endpoint (`POST /api/chat`, `api.py:293-349`) that injects live personnel/project/assignment data into Claude's context. Claude can reason about the schedule but cannot act on it. This doc captures a design discussion about enabling Claude to manipulate assignments.

---

## Q&A

### What would it take for in-app Claude to manipulate assignments (e.g. "rearrange the schedule based on a new crew joining")?

The core addition is **tool use (function calling)** — giving Claude tools backed by the existing API endpoints.

You'd define tools like:

```python
tools = [
    {
        "name": "create_assignment",
        "description": "Assign a person to a project for a date range",
        "input_schema": {
            "type": "object",
            "properties": {
                "personnel_id": {"type": "integer"},
                "project_id": {"type": "integer"},
                "start_date": {"type": "string"},
                "end_date": {"type": "string"},
                "assignment_type": {"type": "string", "enum": ["full", "cascading", "partial"]}
            },
            "required": ["personnel_id", "project_id", "start_date", "end_date", "assignment_type"]
        }
    },
    {
        "name": "delete_assignment",
        "description": "Remove an assignment by ID",
        "input_schema": { "type": "object", "properties": { "assignment_id": {"type": "integer"} }, "required": ["assignment_id"] }
    },
    {
        "name": "update_assignment",
        "description": "Modify assignment dates or type",
        "input_schema": { ... }
    }
]
```

The backend handles a multi-turn loop: send message → if Claude calls tools → (optionally confirm with user) → execute → return results → Claude gives final answer.

---

### How do we prevent Claude from reshuffling the schedule every time we ask it something?

Two layers:

**1. Prompt engineering (most important)**

Add a clear instruction to the system prompt:
> "Only call mutation tools (create/update/delete assignment) when the user *explicitly* asks you to make changes. For questions, analysis, or suggestions, respond with text only — do not call any tools."

Claude's tool use is intent-driven — it won't call `create_assignment` in response to "who's free next week?" because that would be nonsensical.

**2. Confirmation gate before execution (safety net)**

Instead of executing tool calls immediately, return them to the frontend as pending changes:

```json
{
  "message": "Here's the plan: I'll unassign Carlos from Project A and move him to the new crew on Project B...",
  "pending_changes": [
    {"tool": "delete_assignment", "args": {"assignment_id": 42}},
    {"tool": "create_assignment", "args": {"personnel_id": 5, "project_id": 9, ...}}
  ]
}
```

Frontend shows: **"Claude wants to make 3 changes. [Show details] [Approve] [Cancel]"**

Claude never reshuffles silently — the user must explicitly approve.

The scenario model (master vs. draft) is also a natural safety valve: Claude could be configured to only operate on **draft scenarios**, so a human still has to promote to master before changes go live.

---

### How could Claude call our API — doesn't it need network access?

Claude doesn't call your API directly. **Your backend does.**

Claude returns a structured JSON block saying "I want to do X with these parameters." Your Python code reads that and decides what to do — including showing a confirmation dialog before touching the database.

```
User: "rearrange schedule for new crew"
         |
         v
Your backend sends message to Claude API (with tool definitions attached)
         |
         v
Claude responds with a tool_use block:
  {
    "type": "tool_use",
    "name": "create_assignment",
    "input": { "personnel_id": 5, "project_id": 9, "start_date": "2026-03-15", ... }
  }
         |
         v
Your backend reads that, calls insert_assignment() / your own DB functions
         |
         v
Your backend sends the result back to Claude as a tool_result message
         |
         v
Claude generates final text: "Done — I've assigned Carlos to Project B starting March 15th."
```

Think of it like Claude filling out a form. You design the form fields (tool definitions), Claude fills them in, and your code submits the form.

---

### Would the user see the tool use block?

No. The tool use blocks and tool results live entirely in the backend message loop and never reach the client unless you explicitly expose them.

From the user's perspective:

```
User types:  "rearrange schedule for the new crew"
User sees:   [typing indicator...]
User sees:   "Here's what I'm planning to do:
              - Unassign Carlos from Project A (March 20–April 10)
              - Assign Carlos to Project B (March 15–April 5)
              - Assign Yemi to Project A (March 20–April 10)
              Shall I go ahead?"
             [Approve] [Cancel]
```

---

## Rough Implementation Scope

| Component | Change |
|-----------|--------|
| `api.py` `/api/chat` | Add tool definitions to Claude API call; handle `tool_use` stop reason; return pending changes instead of auto-executing |
| `database.py` | No changes needed — mutation functions already exist |
| `index.html` chat UI | Add pending changes panel with approve/cancel buttons; POST approved changes to existing assignment endpoints |
| System prompt | Add explicit "only act when asked" instruction |
