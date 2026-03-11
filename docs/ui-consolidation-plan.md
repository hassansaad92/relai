# UI Consolidation Plan: 5 Tabs → 3 Tabs + Global Chatbot

## Context

The current UI has 5 tabs (Overview, Assignments, Personnel, Projects, Skills) plus a chatbot embedded in the Assignments tab. Information is scattered and redundant — the same assignment/availability data appears on Overview, Personnel, and Assignments tabs. The manager bounces between tabs to piece together what they need. This plan consolidates the layout around the core scheduling workflow.

## New Navigation

```
Current (5 tabs)          →    New (3 tabs)
─────────────────              ─────────────
Overview                  ┐
Assignments               ┘→   Schedule (default landing page)
Personnel                 ┐
Skills                    ┘→   Resources
Projects                  →    Projects
Chatbot (trapped in Assignments) → Global collapsible side panel
```

---

## Tab 1: Schedule (merges Overview + Assignments)

This is the primary workspace. 90% of daily work happens here.

**Layout: Top/Bottom split**

### Top: Gantt Chart (full width, collapsible)
- Keep the existing Plotly bar chart from `renderGantt()`
- Add collapse/expand toggle to minimize when focusing on assignments
- Add **Timeline | Table toggle** — Table view shows the assignments table (Completion, Req. Start, Gap columns) that currently lives on Overview
- Add click interaction: clicking a Gantt bar selects that project in the panel below

### Bottom: Schedule Panels (existing Assignments layout minus chatbot)
- **Left panel (280px):** Project list sorted by start date, with status badges + assignment counts (existing `renderScheduleProjects()`)
- **Right panel (flex):** Selected project detail, assigned personnel, available personnel, assign form (existing `renderScheduleAssignPanel()`)

### What's eliminated
- Overview tab (merged into Schedule)
- Chatbot column from Assignments layout (becomes global panel)
- Redundant assignment data that was spread across 3 tabs

---

## Tab 2: Resources (merges Personnel + Skills)

Reference/management tab for people and skills.

### Section 1: Personnel (primary)
- Keep existing card layout from `renderPersonnelList()`
- Cards show: name, skill tags, availability status, current/next project
- Add filter bar: filter by skill, availability status, text search
- Keep "+ Add Personnel" button

### Section 2: Skills (compact sub-section)
- Show as compact tag cloud or collapsible section below personnel
- Keep "+ Add Skill" button
- Rarely changed, doesn't need its own tab

---

## Tab 3: Projects (stays as-is)

- Keep existing card layout from `renderProjectsList()`
- Add filter bar: filter by award status, schedule status, text search
- Keep "+ Add Project" button

---

## Global Chatbot: Persistent Collapsible Side Panel

- Floating toggle button always visible (in header area, near refresh button)
- Click slides out a right-side overlay panel (~440px)
- Available on every tab, not just Schedule
- Chat history persists across tab switches (already works — `chatHistory` is global)
- Pattern: model after existing `.scenario-panel` overlay approach

---

## Implementation Steps

### Step 1: Restructure HTML views
- Replace 5 `<div class="view">` blocks with 3
- Schedule view = Gantt section above + schedule-layout section below (no chatbot column)
- Resources view = personnel section + skills section together
- Projects view unchanged

### Step 2: Extract chatbot into global overlay
- Move chatbot HTML out of assignments view into a sibling of `.main-content`
- Add toggle button to page header
- Add slide-out CSS (model after `.scenario-panel`)
- JS chat functions are already global — no logic changes needed

### Step 3: Update navigation + routing
- Sidebar: 3 items instead of 5
- Update `showView()`, `viewLoaders`, `getViewFromURL()`, URL routing
- New `loadScheduleData()` merging `loadOverviewData` + `loadAssignmentsData`
- New `loadResourcesData()` merging `loadPersonnelData` + `loadSkillsData`

### Step 4: Gantt/Table toggle
- Toggle button in Gantt section header: "Timeline | Table"
- Timeline = Plotly chart, Table = `renderAssignmentsList()` output
- Preserves the gap analysis info without a separate tab

### Step 5: Gantt → Project click interaction
- Click a Gantt bar → extract project ID → call `selectScheduleProject()`
- Connects visual overview to action panel

### Step 6: Compact Card Grid (Personnel + Projects)

Current cards are full-width stacked rows — wastes space, especially after consolidation reduces the number of tabs. Switch to a responsive multi-column grid of smaller, denser tiles.

**CSS changes to `.card`:**
- Switch container from vertical stack to CSS grid: `grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))`
- Reduce card padding from `10px 14px` → `8px 12px`
- Reduce `.card-title` font-size from `16px` → `14px`
- Reduce `.card-status` padding from `6px 12px` → `3px 8px`
- Reduce `.card-detail` font-size from `13px` → `12px`
- Cap card max-height so content stays uniform — truncate long skill tag lists with overflow ellipsis
- Keep hover lift effect but reduce shadow intensity

**Personnel tiles (Resources tab):**
- Name + status badge on row 1
- Skill tags on row 2 (max 3 visible, +N overflow indicator)
- Available date on row 3
- Current/next project info only shows on hover tooltip or expansion, not inline — keeps tile height consistent

**Project tiles (Projects tab):**
- Name + award/schedule badges on row 1
- Skill tags + elevator/duration meta on row 2
- Requested dates on row 3
- Scheduled dates on row 4 (or combine into one row: "Req: ... → Sched: ...")

**Skills section (Resources tab):**
- Already compact as `.skill-tile` tags — no changes needed

**Breakpoints:**
- `≥1200px`: 3 columns
- `800–1199px`: 2 columns
- `<800px`: 1 column (current behavior)

### Step 7: Filter bars on Resources + Projects
- Text search + dropdown filters above each card grid
- Personnel: filter by skill, availability status
- Projects: filter by award status, schedule status

---

## Data Loading Consolidation

| New Loader | Fetches | Replaces |
|---|---|---|
| `loadScheduleData` | assignments/overview, personnel, projects, assignments | `loadOverviewData` + `loadAssignmentsData` |
| `loadResourcesData` | personnel, skills | `loadPersonnelData` + `loadSkillsData` |
| `loadProjectsData` | projects, skills | unchanged |

---

## Critical Files

- `index.html` — All HTML/CSS/JS (single-file app, ~2400 lines). Only file that changes for UI.
- `api.py` — API endpoints. No changes strictly required but could add a combined endpoint later.
- `docs/design.md` — Color palette reference (`#041e42` / `#f65275`). New UI elements must match.
- `docs/in-app-claude-actions.md` — Chatbot tool-use design doc. Global chatbot panel should align with this.

---

## Verification

1. Load the app → lands on Schedule tab with Gantt + schedule panels
2. Click a Gantt bar → selects corresponding project in panel below
3. Toggle Timeline/Table → switches between chart and gap-analysis table
4. Assign a mechanic from the Schedule tab → Gantt updates
5. Click chatbot button from any tab → side panel slides out
6. Switch tabs with chatbot open → chat history persists
7. Resources tab shows personnel cards + skills section
8. Projects tab shows project cards with filters
9. All 3 nav items route correctly, URL updates work
