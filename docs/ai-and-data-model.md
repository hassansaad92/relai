# AI Integration & Data Model Notes

Reference for how the AI layer works, how data flows, and key things to know when building features around assignments, scenarios, and skills.

---

## How the AI Uses Skills Data

The AI does **not** run any automated matching algorithm. It works entirely through a conversational chatbot interface (`POST /api/chat` in `api.py`).

On every chat request, the backend:
1. Fetches all current personnel, projects, and assignments from the DB
2. Formats them as plain text (including `skills` and `required_skills` fields)
3. Injects everything into a system prompt sent to Claude (Sonnet 4.6)
4. Returns Claude's response to the frontend

**What this means:** Claude does the "matching" through language reasoning at query time. There's no scoring, ranking, or embedding-based similarity — the AI only reasons about skills when a user asks it to (e.g. "Who can work on Project Alpha?").

### What doesn't exist yet (future work)
- Automated skill-match suggestions without user prompting
- Embeddings or vector similarity for skills
- A recommendation engine that scores personnel against project requirements

---

## Data Model: Assignments & Scenarios

### Key Relationship

```
scenarios (id)
    ↑  ← FK lives here, on the assignments side
assignments (scenario_id)
```

Assignments reference scenarios — not the other way around. This means:
- Deleting all assignments leaves the scenarios table fully intact
- Deleting a scenario is blocked by Postgres if any assignments still reference it (FK constraint)
- To delete a scenario, clear its assignments first

### Scenario ID at Runtime

The frontend resolves `currentScenarioId` dynamically at page load by fetching `/api/scenarios` and finding whichever row has `status = 'master'`. All new assignments created through the UI are tagged with this ID.

**Implication:** Clearing the assignments table and repopulating manually will produce correct foreign keys as long as the master scenario row still exists, which it will.

### Testing AI Suggestions from Scratch

To test whether the AI can suggest a full schedule from zero:
1. `DELETE FROM assignments` — safe, no cascade effects
2. Open the chat and ask Claude to suggest assignments based on personnel skills and project requirements
3. Repopulate from the UI; new assignments will correctly reference the existing master scenario

---

## SCD2 History Tables

Personnel, projects, and skills each have a corresponding `_history` table using Slowly Changing Dimension Type 2 (SCD2) — every change creates a new history row with `valid_from` / `valid_to` timestamps and an `is_current` flag.

**Assignments do not have a history table.** Deleting or changing an assignment leaves no audit trail. This is a gap to address when building the assignment management feature.

---

## Assignment CRUD: Current State

| Operation | Status |
|---|---|
| Create assignment | Supported (UI + API) |
| Delete assignment | Supported (API: `DELETE /api/assignments/:id`, UI: remove button) |
| Update assignment | Not yet implemented |
| Assignment history / audit log | Not yet implemented |

When building full assignment management, consider adding:
- `assignments_history` table (matching the SCD2 pattern used elsewhere)
- An update endpoint (`PATCH /api/assignments/:id`)
- UI controls for editing dates and sequence
