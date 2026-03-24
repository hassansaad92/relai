# Expansion Features & Competitive Strategy

---

## The 3 MVP Moat Features

Before anything else: these are the three capabilities that either already exist or must exist to establish RelAI's defensible position. Everything else in this document is expansion. These three ARE the product.

### MVP MOAT 1: Conversational AI Scheduling Engine -- EXISTS

**Status: Built and functional.**

The AI doesn't just display a schedule -- it creates, reasons about, and modifies schedules through natural language. "Schedule the Johnson project next week with Crew B" works. "What happens if I move that to Thursday?" works. The AI understands constraints (skills, availability, business days, fractional assignments) and makes multi-step scheduling decisions that would take a human 30 minutes of spreadsheet work.

This is the product. Not a dashboard with an AI bolted on -- an AI with a dashboard bolted on. ServiceTitan's Atlas answers questions about data. RelAI's AI *is* the scheduling logic. This architectural difference is what makes it hard to replicate: you can't get here by adding a chatbot to a CRUD app.

**What exists today:** Claude-powered chatbot with tool use, incremental scheduling with priority accounts, voice-to-action, skill-aware assignment, business-day logic, scenario versioning (master/draft workflow).

**What needs hardening for MVP launch:**
- Reliability of multi-constraint scheduling (edge cases, conflict resolution)
- Undo/rollback for AI actions (beyond scenario revert)
- Confidence indicators when the AI makes trade-offs ("I moved Project X to fit Project Y -- here's why")

**TO-DO: Context Architecture (critical for scale + moat)**

_This also differentiates it from any old vibe codeable app_

- [ ] **Prompt caching**: Add `cache_control` to system messages. The system prompt + database context is identical across calls in a session. This cuts input costs 90% ($0.30 vs $3.00 per million tokens) and reduces latency. Free money -- implement immediately.
- [ ] **Smart context selection**: Currently every API call dumps ALL personnel, ALL assignments, ALL projects into the prompt (~3-5K tokens now, but grows to 80-120K at 30 personnel / 500 projects). Refactor so the AI gets only what's relevant to the current question. Give it a `query_database` tool so it pulls data on-demand instead of getting everything upfront.
- [ ] **Pre-computed pattern summaries (THE moat layer)**: Run a nightly job that distills historical project data into compact summaries: "Elevator mods average 18% over estimated duration," "Crew B completes mechanical jobs 12% faster," "Pre-war buildings add 3.2 days on average." Inject these summaries (~500 tokens) instead of raw history (~50K tokens). This is the compounding intelligence -- a competitor can clone the code but not the patterns derived from YOUR customers' data. Gets better with every completed project.

**Current context budget (Claude Sonnet 4.6: 200K token window):**
| Scale | Est. Tokens | Status |
|---|---|---|
| 10 personnel, 20 projects | ~3-5K | Easy |
| 30 personnel, 100 projects | ~15-25K | Fine |
| 30 personnel, 500 historical projects | ~80-120K | Tight |
| + contract docs + historical feedback | ~130-170K | Ceiling |

At single-company scale (1-30 people), live data alone won't hit the wall. The pressure comes from accumulated contracts + history. The pattern summary layer solves this: small token footprint, massive value.

---

### MVP MOAT 2: Project-Based Multi-Crew Gantt Scheduling -- EXISTS

**Status: Built and functional.**

_This also differentiates it from any old vibe codeable app_

The data model is fundamentally different from service-visit platforms. RelAI handles multi-day and multi-week projects with overlapping assignments, cascading schedules, partial/fractional-day work, and dual personnel assignments. The Gantt visualization makes this tangible.

This matters because it means RelAI isn't competing with ServiceTitan on their home turf (single truck rolls). It's serving a market they structurally can't serve well: project-based trades work where a job spans days or weeks, involves multiple crew members, and has dependencies.

**What exists today:** Gantt chart (Plotly.js), three assignment types (full, cascading, partial), fractional-day support, business-day-aware scheduling, personnel skill matching, SCD2 audit history.

**What needs hardening for MVP launch:**
- Project dependency chains (Phase 1 must finish before Phase 2 starts)
- Milestone markers on the Gantt (not just assignment blocks)
- Better visual density for 20+ simultaneous projects

**TO-DO: Context Architecture**
- [ ] **Gantt data is frontend-only today.** The Gantt renders from assignment data the frontend already has -- no extra context cost here. But as project count grows past 20+, consider a summary view mode that shows utilization bars instead of individual assignments to keep the UI usable.
- [ ] **Project dependency data model**: Add a `project_dependencies` table (predecessor_id, successor_id, dependency_type). This data is cheap in tokens but essential for the AI to reason about sequencing ("Can't start Phase 2 until Phase 1 finishes"). Without it, the AI schedules each project independently -- fine for 10 projects, wrong for 50.

---

### MVP MOAT 3: Contract-Aware AI (RAG Engine) -- DOES NOT EXIST YET

**Status: Not built. This is the #1 build priority.**

_This also differentiates it from any old vibe codeable app!_

This is the feature that transforms RelAI from "a nice AI scheduling tool" into "the operations brain for my company." Upload a PDF contract, and the AI can answer: "What are our obligations on the 5th Ave project?" "When's the penalty deadline?" "What scope did the sub agree to?"

No field service tool -- not ServiceTitan, not Jobber, not Housecall Pro -- can do this. It bridges the gap between "what we promised" (the contract) and "what we scheduled" (the Gantt). Today, that gap lives in an ops manager's head, in email threads, and in filing cabinets.

**Why this must be in the MVP:** Without it, RelAI is a better-than-spreadsheet scheduling tool. With it, RelAI is the single source of truth for the entire operation. It's the difference between a tool people use and a system people depend on.

**What needs to be built:**
- Document upload per project (PDF, DOCX)
- Embedding pipeline (chunk, vectorize, store -- Supabase pgvector or external vector store)
- RAG retrieval integrated into the chatbot's context
- Source citations in AI responses ("Based on Section 4.2 of the contract...")
- Structured extraction: auto-populate project fields (dates, scope, penalties) from contract text

**TO-DO: Context Architecture (this is where context management matters most)**
- [ ] **RAG, not stuffing**: Contract docs NEVER go into the system prompt in full. A single contract PDF can be 10-50 pages (5K-25K tokens). With 20 contracts that's 100K-500K tokens -- way past the context window. Instead: chunk each doc into ~500-token segments, embed with an embedding model, store vectors in Supabase pgvector. Per query, retrieve only the top 5-10 most relevant chunks (~2,500-5,000 tokens). This keeps contract context lightweight no matter how many docs are uploaded.
- [ ] **Structured extraction on upload (one-time cost)**: When a contract is uploaded, run a one-time Claude call to extract key fields (dates, scope, penalties, deliverables, parties) into structured database columns. This means the AI can reference contract metadata without hitting the vector store for simple questions like "When does the 5th Ave penalty kick in?" -- it's just a database field.
- [ ] **Hybrid retrieval**: For the chatbot, use a two-pass approach: (1) check structured fields first (fast, zero token cost), (2) only hit the vector store if the question requires deep contract reasoning ("What exactly does Section 4.2 say about our liability?"). This minimizes API cost for 80% of queries.
- [ ] **Per-project context scoping**: When the user asks about a specific project, only retrieve contract chunks for THAT project. Never load all contracts into context. The AI already knows which project is being discussed from the conversation -- use that to scope the retrieval.

**Context budget for RAG queries:**
| Component | Tokens | Notes |
|---|---|---|
| System prompt + instructions | ~2,000 | Static, cached |
| Live scheduling context (relevant subset) | ~3,000-8,000 | Smart selection, not full dump |
| Retrieved contract chunks (top 5-10) | ~2,500-5,000 | Per-query RAG retrieval |
| Pattern summaries (from Moat 1) | ~500 | Pre-computed, tiny |
| Conversation history | ~2,000-5,000 | Recent turns only |
| **Total per query** | **~10,000-20,000** | Fits easily in 200K, costs ~$0.03-0.06/query |

This architecture means context costs stay flat regardless of how many contracts, projects, or historical records accumulate. The data grows in the database and vector store; the prompt stays lean.

---

### Why These 3 and Not Others?

These three create a **closed loop** that no competitor has:

```
Contract (what we promised)
    ↓ RAG Engine parses it
Schedule (what we planned)
    ↓ AI Scheduler builds it
Execution (what actually happened)
    ↓ feeds back into better scheduling
```

The contract grounds the schedule in reality. The AI scheduler makes the schedule adaptive. The Gantt makes it visible. Together, they replace the ops manager's mental model with a shared, queryable, AI-powered system. Every other feature in this document is an extension of this loop.

---

## Pricing & Unit Economics

### The Anti-ServiceTitan Pricing Model

ServiceTitan charges **$250-500/tech/month** with opaque pricing, 12-month contracts, and $10-25K implementation fees. A 10-technician shop pays **$30,000-$60,000/year** before add-ons. This prices out the entire 1-15 person market -- which is the majority of trades businesses in the US.

RelAI's pricing should be **per-company, not per-technician**. This is both a competitive weapon and an alignment with how small companies think about software ("What does this cost me per month?" not "What does this cost per head?").

### Proposed Tier Structure

| Tier | Monthly Price | Annual Price | Target | Includes |
|---|---|---|---|---|
| **Starter** | $79/mo | $790/yr (save ~$160) | 1-5 person shops | AI scheduling, Gantt, up to 5 personnel, 3 active projects, basic chatbot |
| **Growth** | $149/mo | $1,490/yr (save ~$300) | 6-15 person companies | Everything in Starter + unlimited personnel/projects, contract RAG (up to 20 docs), scenario versioning, sales intake portal |
| **Pro** | $249/mo | $2,490/yr (save ~$500) | 16-30 person companies | Everything in Growth + unlimited contract docs, multi-scenario comparison, daily dispatch, workflow automations, priority support |

### Why These Numbers Work

**For the customer:**
- A 10-person elevator contractor currently pays $0 (spreadsheets) or $30K-60K/yr (ServiceTitan). RelAI Growth at $1,490/yr is a no-brainer.
- Even the smallest 2-person shop can justify $79/mo if it saves the owner 5 hours/week of scheduling and phone calls. That's less than 2 hours of billable labor.
- The per-company model means adding your 6th mechanic doesn't trigger a price increase -- it rewards growth.

**For RelAI (cost structure ballpark):**

| Cost Component | Per-Customer/Month Estimate | Notes |
|---|---|---|
| AI/LLM API costs | $5-25 | Depends on usage volume; Claude API for chat + RAG queries + scheduling actions. Heavy users (50+ chatbot interactions/day) push toward $25. Caching and prompt optimization reduce this over time. |
| Vector DB / embeddings | $1-5 | pgvector on Supabase is near-zero at small scale. Scales with document volume. |
| Supabase hosting | $2-8 | Database, auth, storage. Shared infrastructure across customers. |
| Infrastructure (compute, CDN) | $3-10 | FastAPI hosting, static assets, background jobs. |
| **Total variable cost** | **$11-48/customer/mo** | |

**Gross margin by tier:**

| Tier | Revenue | Est. Variable Cost | Gross Margin | Margin % |
|---|---|---|---|---|
| Starter ($79) | $79 | ~$15 | ~$64 | ~81% |
| Growth ($149) | $149 | ~$28 | ~$121 | ~81% |
| Pro ($249) | $249 | ~$42 | ~$207 | ~83% |

These are healthy SaaS margins. The key variable is AI API cost, which will decrease over time as models get cheaper and caching/fine-tuning reduce per-query costs.

### Competitive Positioning by Price

```
ServiceTitan   ████████████████████████████████████████  $30,000-60,000/yr (10-tech shop)
Jobber Pro     ████████                                  $5,988/yr (per-user pricing)
Housecall Pro  ██████                                    $3,588/yr (per-user pricing)
RelAI Growth   ██                                        $1,490/yr (flat)
RelAI Starter  █                                         $790/yr (flat)
Spreadsheets   ·                                         $0 (but costs hours/week)
```

RelAI slots in just above free tools and 10-20x below ServiceTitan. The value proposition is: "You get 80% of what an enterprise tool offers at 5% of the cost, and it actually works for a company your size."

### Revenue Milestones (Sanity Check)

| Milestone | Customers | Mix Assumption | ARR |
|---|---|---|---|
| Early traction | 50 | 60% Starter, 30% Growth, 10% Pro | ~$62K |
| Product-market fit | 200 | 40% Starter, 40% Growth, 20% Pro | ~$310K |
| Growth phase | 1,000 | 30% Starter, 45% Growth, 25% Pro | ~$1.8M |
| Scale | 5,000 | 20% Starter, 50% Growth, 30% Pro | ~$10.2M |

### Pricing Levers to Watch

- **AI usage-based add-on**: If power users burn through significantly more API calls, consider a usage cap on Starter with a per-query overage or upgrade nudge (not a hard wall).
- **Contract document volume**: RAG storage and embedding costs scale with documents. The 20-doc cap on Growth is a natural upgrade trigger.
- **Annual discount**: 2 months free on annual plans (~17% discount) is industry standard and improves cash flow predictability.
- **Free trial**: 14-day full-access trial with AI-guided onboarding. The onboarding IS the trial -- if the AI can set up their company in an hour, they're hooked.

---

## Competitive Landscape: Why Not Just Use ServiceTitan?

ServiceTitan is the 800-lb gorilla in field service management (~$500M+ ARR, IPO'd Dec 2024). Understanding where they dominate and where they fall short is essential for positioning RelAI.

### Where ServiceTitan Wins (Don't Compete Head-On)

- **End-to-end service visit workflow**: Booking > dispatch > invoice > payment is deeply integrated
- **Pricebook & flat-rate pricing**: Mature, trades-specific pricing engine
- **Marketing attribution**: Call tracking, campaign ROI, review solicitation
- **Enterprise scale**: Built for 20-200+ technician fleets with dedicated office staff
- **Accounting integrations**: QuickBooks, payment processing, financing

### Where ServiceTitan Bleeds (Our Opportunity)

| ServiceTitan Pain Point | RelAI Advantage |
|---|---|
| 2-6 month implementation, $10-25K setup | AI-guided setup, operational in days |
| $250-500/tech/month, opaque pricing | Transparent, accessible pricing for small teams |
| Rigid workflows that dictate how you work | Conversational AI that adapts to how you already work |
| Built for service visits, not projects | Built for multi-day/multi-week project scheduling |
| Overkill for teams under 15 techs | Purpose-built for 1-30 person companies |
| Reactive AI (Atlas answers questions) | Proactive AI (flags problems before you ask) |
| No contract intelligence | RAG-powered contract understanding |
| No scenario planning | Multi-scenario schedule comparison |

---

## RelAI's Moat Opportunities

These are the capabilities that would be genuinely hard for ServiceTitan (or similar incumbents) to replicate, and where we should concentrate investment.

### MOAT 1: Conversational Scheduling Intelligence

ServiceTitan added "Atlas" but it's a query layer on top of a traditional CRUD app. RelAI's core differentiator is that **the AI IS the scheduling engine** -- it doesn't just read the schedule, it reasons about constraints, trade-offs, and ripple effects in natural language. This is architecturally different and hard to bolt onto a legacy system.

*Deepening the moat:* Every scheduling decision the AI makes builds a feedback loop. Over time, RelAI learns that "elevator mods in pre-war buildings take 20% longer" or "Crew B is 15% faster on plumbing jobs." This institutional knowledge compounds and becomes impossible to replicate.

### MOAT 2: Instant Time-to-Value

ServiceTitan's 2-6 month onboarding is structural -- their system is complex because it tries to be everything. RelAI can be the "just start talking to it" alternative. Upload a contract, describe your crew, and you have a schedule. This simplicity is a feature, not a limitation.

### MOAT 3: Project-Based Scheduling (Not Service Visits)

ServiceTitan is optimized for the "truck roll" model: single-visit service calls. RelAI is built for **multi-day, multi-crew projects** with dependencies, overlapping assignments, and cascading schedules. This is a fundamentally different data model that can't be patched onto a service-visit platform.

### MOAT 4: Contract-Aware AI

No major field service tool can ingest a PDF contract and reason about obligations, penalties, and scope. This bridges the gap between "what did we promise?" and "what did we schedule?" -- a gap that currently lives in an ops manager's head.

### MOAT 5: Small Company Economics

ServiceTitan's unit economics require $250-500/tech/month to work. RelAI can serve the massive underserved market of 1-30 person shops that can't justify (or survive) that cost structure.

---

## Feature Roadmap

### Legend

| Tag | Meaning |
|---|---|
| **MOAT** | Core differentiator, hard to replicate |
| **OVERLAP** | ServiceTitan already does this well -- build only if essential, don't lead with it |
| **TABLE STAKES** | Expected by users but not a differentiator |
| **BRIDGE** | Connects two personas (Sales <> Ops <> Field) |

---

## Part A: Ops Manager Features

### 1. Contract RAG Engine -- MOAT

Integrate a document ingestion pipeline (PDF/DOCX) so the AI assistant can answer questions against uploaded contracts and work orders. Users upload project documents, which get chunked and embedded into a vector store. The chatbot answers queries like "What are my obligations for Project X?" or "What's the penalty clause on the elevator install at 5th Ave?" by retrieving relevant contract sections.

**Why this is a moat:** No field service tool does this. ServiceTitan has no document intelligence. This turns RelAI from a scheduling tool into an operations brain.

**Key deliverables:**
- Document upload UI per project
- Embedding pipeline (chunking, vectorization, storage)
- RAG-augmented chatbot responses with source citations

---

### 2. Automated Bill of Materials (BOM) Generation -- MOAT

Given a project's type and contract scope, auto-generate a procurement checklist from a library of standard templates (e.g., "Elevator Modernization" has ~40 standard line items). The AI pulls from the contract RAG engine to flag non-standard materials.

**Why this is a moat:** Combines contract intelligence + domain templates + AI reasoning. ServiceTitan has inventory management but no AI-driven BOM generation from contracts.

**Key deliverables:**
- BOM template library (CRUD management)
- AI-assisted BOM generation from project metadata + contract docs
- Export to CSV/PDF

---

### 3. Procurement Lead-Time Tracker & Critical Path Alerts -- MOAT

Track material lead times per BOM line item and compare against committed start dates. Surface a dashboard widget flagging at-risk projects (e.g., "Project starts in 2 weeks but switchgear has a 6-week lead time"). Mark procurement-blocked projects on the Gantt view.

**Why this is a moat:** Connects procurement reality to schedule feasibility. ServiceTitan's inventory module is complex and manual; it doesn't proactively flag schedule-procurement conflicts.

**Key deliverables:**
- Lead-time field per BOM item (manual entry initially, supplier API later)
- Critical-path risk calculation (start date minus lead time)
- Home page alert widget and Gantt color coding for at-risk projects

---

### 4. Sales-to-Ops Handoff Pipeline -- BRIDGE

A structured intake form where salespeople enter new project details (scope, customer, urgency, required skills, estimated duration). Submissions land in an Ops review queue. Eliminates the morning information gap between Sales (9 AM) and Ops (6 AM).

**Overlap note:** ServiceTitan has CRM and job creation workflows. However, their model is "office staff creates the job." RelAI's version is AI-mediated: the chatbot can validate, enrich, and flag issues in the handoff automatically.

**Key deliverables:**
- Sales intake form (standalone page or shareable link)
- Ops review queue with approve/reject/edit workflow
- Auto-creation of project record upon approval

---

### 5. Geo-Aware Travel Time Scheduling -- OVERLAP (partial)

Add project locations and calculate travel time between consecutive assignments for the same crew. The Gantt chart shows travel blocks as distinct segments.

**Overlap note:** ServiceTitan's Dispatch Pro already does GPS-based route optimization with traffic awareness. However, their model is single-visit dispatch, not multi-day project sequencing. Our version factors travel into multi-week project planning, which is different enough to justify building.

**Key deliverables:**
- Location field on projects (geocoded address)
- Travel time calculation between sequential assignments
- Travel buffer blocks on the Gantt chart
- AI assistant awareness of travel constraints during scheduling

---

### 6. Crew Workload Balancing Dashboard -- TABLE STAKES

A dedicated analytics view showing workload distribution across personnel over a rolling time window. Highlights overloaded mechanics, underutilized crew members, and overtime trends.

**Overlap note:** ServiceTitan has extensive reporting and KPI dashboards. Our differentiator is that the AI doesn't just show the data -- it recommends specific rebalancing actions via natural language.

**Key deliverables:**
- Workload heatmap (personnel x week)
- Utilization percentage per person
- AI-powered rebalancing suggestions via chatbot

---

### 7. Customer Urgency & SLA Scoring -- TABLE STAKES

Assign urgency tiers and SLA deadlines to projects. The scheduling engine uses these as weighted constraints. The home page shows countdowns for projects approaching SLA breach.

**Overlap note:** ServiceTitan has priority tagging and job urgency. Our version is deeper because the AI actively reshuffles schedules to prevent SLA breaches rather than just flagging them.

**Key deliverables:**
- Urgency tier and SLA deadline fields on projects
- Priority-weighted scheduling logic in the AI optimizer
- SLA countdown widget on home page

---

### 8. Multi-Scenario Comparison View -- MOAT

Side-by-side comparison of draft schedules. Ask the AI to generate alternatives under different assumptions ("What if we prioritize the hospital project?" vs. "What if we minimize travel?") and visually compare Gantt charts, utilization stats, and cost implications.

**Why this is a moat:** No field service tool offers AI-generated schedule alternatives with visual comparison. This is "what-if" analysis that previously required a spreadsheet wizard. Extends our existing scenario versioning system.

**Key deliverables:**
- Side-by-side Gantt rendering for 2-3 scenarios
- Summary diff panel (what changed between scenarios)
- "Promote to master" action from comparison view

---

### 9. Daily Dispatch & Crew Notifications -- TABLE STAKES

Generate a daily dispatch sheet per crew: today's assignments, project address, contact info, special instructions, materials needed. Deliver via email, SMS, or mobile-friendly web view.

**Overlap note:** ServiceTitan's mobile app handles this end-to-end (including payments, photos, signatures). Don't try to replicate the full field technician app. Focus on a lightweight, zero-friction daily briefing that works without installing anything.

**Key deliverables:**
- Daily dispatch generation (auto-triggered or on-demand)
- Delivery channels (email and/or SMS)
- Mobile-friendly dispatch view (no app install required)
- Read-receipt tracking on home page

---

### 10. Post-Project Feedback Loop & Schedule Accuracy Tracking -- MOAT

Capture actual vs. planned duration, scope changes, and crew debriefs after project completion. Feed this data back into the AI's scheduling model to improve future estimates.

**Why this is a moat:** This creates a learning loop that gets smarter with every completed project. ServiceTitan tracks job costing but doesn't feed variance data back into scheduling predictions. Over time, this becomes proprietary institutional knowledge encoded in the AI.

**Key deliverables:**
- Project completion form (actual duration, delay reasons, crew notes)
- Historical accuracy dashboard (planned vs. actual trends)
- AI model calibration: feed historical variance into future duration estimates

---

## Part B: Sales Rep Features

### 11. Centralized Project Intake Portal -- BRIDGE

A dedicated sales-facing interface for entering core project metadata: Customer Name, Building Address, Project Type, Desired Start Date, and Contractual Start Date. The distinction between desired and contractual dates captures customer urgency upfront.

**Key deliverables:**
- Sales intake form with structured fields (customer, address, type, dates)
- Desired vs. Contractual start date fields
- Validation rules (required fields, date logic)
- Auto-generated project record in "Pending Ops Review" status

---

### 12. Contract Upload & AI Parsing -- MOAT

Allow salespeople to upload PDF contracts directly into a project record. The system uses the Contract RAG Engine (#1) to parse the document, extract key terms, and store a structured summary as the project's "source of truth."

**Why this is a moat:** Eliminates manual transcription. The AI reads the contract so nobody has to.

**Key deliverables:**
- Drag-and-drop PDF upload on the project intake form
- AI-powered extraction of key contract fields (scope, dates, penalties, deliverables)
- Editable structured summary for sales rep to verify before submission

---

### 13. Account Tiering & National Account Flagging -- TABLE STAKES

Link projects to Customer IDs and assign account tiers (National Account, VIP, Standard). Auto-flag high-priority accounts during scheduling.

**Overlap note:** ServiceTitan has customer management and tagging. Our differentiator is tier-aware AI scheduling (VIP accounts automatically get priority in the optimizer, not just a colored label).

**Key deliverables:**
- Customer entity with tier field (National, VIP, Standard)
- Project-to-Customer linkage
- Auto-tagging of projects based on account tier
- Tier-aware sorting in Ops review queue

---

### 14. Sales Self-Service Status Checker -- BRIDGE

A chatbot command where sales reps check real-time status of their submitted projects. "What's the status of the 5th St elevator repair?" returns Scheduled/Unscheduled/Pending Procurement with crew assignment and projected dates.

**Why this matters:** Eliminates the #1 reason salespeople call Ops managers. ServiceTitan has customer portals but not AI-powered natural language status queries across roles.

**Key deliverables:**
- Sales-role chatbot access with scoped permissions (read-only on schedules)
- Natural language status queries
- Response includes crew assignment, projected dates, and blockers

---

### 15. Project Tile Dashboard for Sales -- TABLE STAKES

Visual dashboard showing all of a sales rep's submitted projects as cards/tiles. Color-coded by status, sortable by urgency, date, or customer.

**Key deliverables:**
- Tile/card layout with project summary info
- Color coding by status (green = scheduled, yellow = pending, red = blocked)
- Filtering by customer, status, date range

---

### 16. Automated Status Change Notifications -- TABLE STAKES

Proactive push notifications when projects hit key milestones. Delivered via in-app notification, email digest, or webhook to Slack/Teams.

**Overlap note:** ServiceTitan has notification systems. Keep ours lightweight and configurable rather than trying to match their notification infrastructure.

**Key deliverables:**
- Event triggers on project status transitions
- Notification preferences per user (in-app, email, Slack)
- Daily digest option for low-urgency updates

---

### 17. Customer-Facing Status Reports -- BRIDGE

One-click generation of a polished status report a sales rep can forward to their customer. Auto-populated from live schedule data.

**Key deliverables:**
- Report template with company branding
- Auto-populated fields from project and schedule data
- Export as PDF or send directly via email

---

### 18. Sales Pipeline-to-Schedule Forecasting -- MOAT

The chatbot answers "If I close a 3-week elevator modernization next week, when's the earliest we could start?" by looking at current crew availability, skill requirements, and the pending project queue.

**Why this is a moat:** This bridges sales and operations in real time. No field service tool lets a salesperson query scheduling capacity conversationally during a sales call. This is the "AI-native" version of what would otherwise require a phone call to Ops.

**Key deliverables:**
- Capacity forecast query via chatbot
- "Earliest available start" calculation based on current schedule load
- Skill-aware capacity ("plumbing crews available in 2 weeks, elevator crews booked for 6")
- Confidence indicator (firm vs. tentative based on pending projects)

---

### 19. Multi-Project Customer View -- TABLE STAKES

Consolidated view of all projects for a single customer, showing full history and active engagements.

**Key deliverables:**
- Customer detail page with project history timeline
- Active/completed/pending project breakdown
- Chatbot query support ("Show me all projects for Acme Corp")

---

### 20. Sales-Ops Feedback Channel -- BRIDGE

A structured communication layer within each project where sales and ops can exchange notes. The chatbot summarizes threads on demand.

**Key deliverables:**
- Per-project comment/note thread visible to both Sales and Ops roles
- @mention notifications for urgent items
- Chatbot summarization of conversation threads

---

## Part C: AI-First Project Management Platform Features (21-30)

*Expanding the vision: RelAI as the AI-native project management platform for small companies across trades and services, not just elevator/mechanical.*

---

### 21. AI-Guided Company Onboarding -- MOAT

A conversational onboarding flow where the AI asks questions to set up the entire system: "Tell me about your team," "What types of projects do you do?", "Upload a recent contract and I'll figure out the rest." No forms, no configuration wizards, no 6-month implementation. The AI infers project types, skill taxonomies, and scheduling constraints from natural conversation and uploaded documents.

**Why this is a moat:** ServiceTitan's #1 complaint is 2-6 month onboarding. Making setup conversational and AI-driven is the single biggest wedge for small company adoption. This is hard to retrofit onto a traditional CRUD platform.

**Key deliverables:**
- Conversational setup wizard via chatbot
- AI-inferred skill taxonomy from crew descriptions
- Auto-generated project templates from uploaded contracts
- "Operational in under an hour" target

---

### 22. Natural Language Workflow Automation -- MOAT

Let users define automations in plain English: "When a project is 3 days from starting and no materials have been ordered, alert me." "Every Monday morning, send me a summary of the week's schedule." "If a crew finishes early, suggest pulling forward the next project." No Zapier, no if-then builders -- just describe what you want.

**Why this is a moat:** This replaces the entire workflow automation category (Zapier, Make, ServiceTitan's rigid built-in rules) with something any non-technical ops manager can create in 30 seconds. The AI translates intent into event triggers and actions.

**Key deliverables:**
- Natural language automation definition via chatbot
- Event trigger system (status changes, date thresholds, capacity changes)
- Action library (notify, reschedule, create task, send report)
- Automation management UI (view, edit, disable active automations)

---

### 23. AI Morning Briefing -- MOAT

Every morning (configurable time), the AI generates a personalized briefing for each role. The Ops Manager gets: today's dispatch summary, at-risk projects, crew availability gaps, procurement alerts, and suggested actions. The Sales Rep gets: project status updates, upcoming customer milestones, and capacity windows for new sales. No dashboards to check -- the AI comes to you.

**Why this is a moat:** Flips the paradigm from "pull" (go check dashboards) to "push" (the AI tells you what matters). ServiceTitan requires you to navigate to reports. RelAI distills the whole system into a 2-minute morning read.

**Key deliverables:**
- Role-based briefing generation (Ops, Sales, Field)
- Delivery via email, SMS, or in-app
- Actionable items with one-tap responses ("Approve this schedule change?")
- Customizable briefing preferences

---

### 24. Voice-First Operations -- MOAT

Full voice interface for hands-free operation. An ops manager driving to a job site can say "Move the Johnson project to next week and assign Crew B" and the AI executes it. A field crew lead can say "We're done with Phase 1, what's next?" and get routed. Builds on existing voice-to-action capability.

**Why this is a moat:** ServiceTitan's Atlas has voice, but it's query-focused. RelAI's voice interface takes actions and handles multi-step scheduling operations conversationally. This is especially valuable for the small-company persona who IS the ops manager AND is in the field.

**Key deliverables:**
- Voice command processing for scheduling operations
- Confirmation loop for destructive/irreversible actions
- Hands-free mode (continuous listening with wake word)
- Field crew voice check-in/check-out

---

### 25. Template Marketplace & Industry Packs -- MOAT

Pre-built configuration packs for specific trades: "Elevator Contractor Pack" includes project templates, skill taxonomies, BOM templates, and scheduling rules. "General Contractor Pack," "HVAC Service Pack," "Plumbing Pack," etc. Community-contributed templates that encode industry best practices. New users select their trade and get a pre-configured system.

**Why this is a moat:** Encodes domain expertise into reusable, shareable configurations. ServiceTitan has industry-specific features but they're baked into a monolithic product. RelAI's approach is modular -- each pack is a layer of AI context and templates that can be customized.

**Key deliverables:**
- Template pack format (project types, skills, BOMs, scheduling rules)
- Pre-built packs for 5-10 common trades
- Pack import/export system
- Community contribution mechanism (later phase)

---

### 26. Lightweight Job Costing -- TABLE STAKES (but positioned differently)

Track labor hours and material costs per project against the original estimate. The AI flags cost overruns in real time: "Project X is 60% complete but has consumed 80% of the labor budget." Not a full accounting system -- just enough visibility for an owner-operator to know if a project is making or losing money.

**Overlap note:** ServiceTitan has deep job costing. Our version is intentionally simpler -- no accounting integration needed, no pricebook management. Just "what did we estimate, what did we spend, are we on track?" This targets the small company that currently tracks this in a spreadsheet (or doesn't track it at all).

**Key deliverables:**
- Estimated vs. actual labor hours per project
- Material cost tracking per project
- AI-generated cost alerts ("Project X labor is trending 25% over estimate")
- Simple profit/loss per project view

---

### 27. Subcontractor Coordination -- BRIDGE

For projects that involve subcontractors, provide a limited-access portal where subs can view their assigned scope, confirm availability, and report progress. The AI factors sub availability and lead times into the master schedule. "Are we waiting on the electrician before we can start Phase 3?" becomes a question the AI can answer.

**Key deliverables:**
- Subcontractor entity with limited portal access
- Sub availability and confirmation workflow
- Integration of sub timelines into master Gantt
- AI awareness of subcontractor dependencies in scheduling

---

### 28. Smart Document Generation -- MOAT

AI-generated project documents from schedule and contract data: change orders, progress reports, completion certificates, punch lists. "Generate a change order for adding 2 weeks to the Johnson project" produces a formatted document with the right dates, costs, and contract references already filled in.

**Why this is a moat:** Combines contract intelligence (RAG) + schedule data + document generation. No field service tool can auto-generate contractual documents that reference both the schedule and the original contract terms.

**Key deliverables:**
- Document templates (change order, progress report, completion cert, punch list)
- AI auto-fill from project, schedule, and contract data
- Edit and approve workflow before finalizing
- PDF export with company branding

---

### 29. Cash Flow Forecasting from Schedule -- MOAT

Use the schedule to project cash flow: "Based on current project timelines and payment terms, here's your expected revenue by month for the next quarter." Factor in milestone-based payments, retainage, and procurement costs. An owner-operator can ask "Can I afford to hire another mechanic in Q3?" and get a data-driven answer.

**Why this is a moat:** Connects scheduling data to financial planning in a way that typically requires a CFO or accountant. For a 10-person company, this is transformative. ServiceTitan has revenue reporting but not AI-driven cash flow forecasting from schedule projections.

**Key deliverables:**
- Payment milestone tracking per project (deposit, progress, completion, retainage)
- Monthly cash flow projection from active + scheduled projects
- "What-if" financial scenarios tied to schedule scenarios
- AI-powered answers to financial capacity questions

---

### 30. Owner Dashboard & Business Health Score -- TABLE STAKES (but AI-enriched)

A single-screen view for the company owner: are we profitable, are crews utilized, are customers happy, are we growing? A composite "business health score" that the AI explains in plain language: "Your health score dropped this week because two projects are behind schedule and crew utilization fell below 70%."

**Key deliverables:**
- Composite health score (utilization, profitability, schedule adherence, customer satisfaction)
- AI-generated plain language explanation of score changes
- Trend lines (week over week, month over month)
- Recommended actions ("Consider reassigning Crew A to reduce idle time")

---

## Summary: Build Priority by Strategic Value

### Build First (Moat Features -- Defensible Differentiation)
1. Contract RAG Engine (#1, #12)
2. AI-Guided Onboarding (#21)
3. Natural Language Workflow Automation (#22)
4. AI Morning Briefing (#23)
5. Multi-Scenario Comparison (#8)
6. Post-Project Feedback Loop (#10)
7. Sales Pipeline-to-Schedule Forecasting (#18)

### Build Second (Bridge Features -- Cross-Persona Value)
8. Sales-to-Ops Handoff Pipeline (#4, #11)
9. Sales Self-Service Status Checker (#14)
10. Sales-Ops Feedback Channel (#20)
11. Subcontractor Coordination (#27)

### Build Third (Table Stakes -- Expected But Not Differentiating)
12. Account Tiering (#13)
13. Daily Dispatch (#9)
14. Notifications (#16)
15. Project Tile Dashboard (#15)
16. Customer View (#19)
17. Workload Balancing (#6)

### Build Carefully (High Overlap with ServiceTitan)
18. Geo-Aware Travel (#5) -- build the project-sequencing version, not the truck-roll version
19. Job Costing (#26) -- keep it simple, don't become an accounting tool
20. Customer-Facing Reports (#17) -- lightweight, not a full CRM reporting suite

---

## Market Analysis & Go-to-Market Strategy

### The Addressable Universe

There are **400,000-600,000 small trade contractor firms** (1-30 employees) in the US doing project-based work in the 1-30 day range. These are not service-call businesses -- they're companies that bid on jobs, schedule crews across multiple concurrent projects, and manage multi-day engagements.

### Market Sizing

| Level | Definition | Firms | ARR Potential |
|---|---|---|---|
| **TAM** | All US specialty trade firms (1-30 employees) doing multi-day project work | ~500,000 | ~$1.8B at $3,600/yr avg |
| **SAM** | Firms with enough complexity to benefit from AI scheduling (2+ crews, multiple concurrent jobs) and willingness to pay | ~150,000 | ~$540M at $3,600/yr avg |
| **SOM** | Realistic 5-year capture at 5-8% SAM penetration | 7,500-12,000 | **$27-43M ARR** |

### Can We Target Only Elevator Right Now?

**Yes, and we should.** But understand the math:

- Total US elevator/escalator contractor firms: ~2,215
- Independent small shops (1-30 employees): **~800-1,200**
- Realistic penetration (20-30% of independents): **160-360 customers**
- At Growth tier ($149/mo): **$286K-$644K ARR**

The elevator vertical is a **proof-of-concept market, not a business-scale market.** It's perfect for validating product-market fit -- RelAI was literally built for it, the domain knowledge is baked in, and you can sell to every elevator contractor in the US through NAEC (National Association of Elevator Contractors) and IUEC union networks. But it caps out under $1M ARR.

**The elevator vertical buys you:**
- 5-10 reference customers who genuinely love the product
- Case studies with real scheduling complexity (multi-week mods, multi-crew installs)
- Proof that the AI actually works in a high-stakes, regulated environment
- Credibility when you walk into adjacent trades ("We schedule elevator modernizations -- your commercial electrical projects are simpler")

### Where Do We Expand? Trade-by-Trade Readiness

The key question: **which trades have project work in the 1-30 day range, enough scheduling complexity to need AI, AND are underserved by existing tools?**

#### Tier 1: Expand Here First (High fit, minimal product changes)

| Trade | US Firms (1-30 emp) | Typical Project Duration | Why It Fits Now |
|---|---|---|---|
| **Fire Protection / Sprinkler** | ~12,000-15,000 | 1-6 weeks | Almost identical workflow to elevator: multi-day installs, skill-specific crews (sprinkler fitters), phased projects, inspection-driven timelines. Small fragmented market that ServiceTitan doesn't serve. |
| **Low-Voltage / AV / Security** | ~10,000-18,000 | 2 days - 8 weeks | Structured cabling and AV install is pure project work. Small crews, multiple concurrent jobs, no dominant scheduling tool. These companies currently use spreadsheets or basic job boards. |
| **Solar Installation** | ~8,000-9,500 | 1-4 weeks | Fast-growing market (803% growth since 2006). Each install is a discrete project with permitting, procurement, and crew scheduling. Companies are tech-forward and used to software. |

**Combined Tier 1 market: ~30,000-42,500 firms. At 10% penetration and $149/mo avg: $5.4M-$7.6M ARR.**

#### Tier 2: Expand Here Next (Good fit, some product adaptation needed)

| Trade | US Firms (1-30 emp) | Typical Project Duration | What Needs to Change |
|---|---|---|---|
| **Electrical (commercial)** | ~80,000-100,000 | 2-8 weeks | Phased project support needed (rough-in, trim, commissioning happen at different points in a building's construction timeline). Need to handle GC-driven schedules where the electrical sub doesn't control the start date. |
| **HVAC Installation (commercial)** | ~40,000-60,000 | 1-12 weeks | Same phased-work pattern as electrical. Need to distinguish HVAC install (project) from HVAC service/repair (service call -- not our market). |
| **Glass / Glazing** | ~18,000-22,000 | 3 days - 12 weeks | Curtainwall and storefront work is highly project-based. Procurement lead times for custom glass are long -- our lead-time tracker becomes a killer feature here. |
| **Commercial Roofing** | ~22,000-28,000 | 3 days - 4 weeks | Weather-dependent scheduling adds a constraint the AI would need to handle. Otherwise very similar: crews, multi-day jobs, concurrent projects. |

**Combined Tier 2 market: ~160,000-210,000 firms. At 5% penetration and $149/mo avg: $14.3M-$18.8M ARR.**

#### Tier 3: Later Expansion (Large market, more product work required)

| Trade | US Firms (1-30 emp) | Typical Project Duration | Complexity |
|---|---|---|---|
| **Concrete / Masonry** | ~65,000-75,000 | 3 days - 8 weeks | Weather and curing-time dependencies. Work is highly dependent on GC sequencing. |
| **Commercial Painting** | ~25,000-40,000 | 3 days - 4 weeks | Simpler scheduling needs -- may not justify AI-level tooling for many shops. |
| **Flooring** | ~80,000-95,000 | 2 days - 4 weeks | Massive market but many jobs are simple enough that a whiteboard works. Higher-end commercial flooring (hospitals, airports) has real complexity. |
| **Plumbing (commercial)** | ~25,000-40,000 | 4-20 weeks (phased) | Long, GC-dependent timelines. Similar challenges to electrical. |
| **Small General Contractors** | ~50,000-80,000 | 2-12 weeks | GCs manage subs, not just their own crews. Need subcontractor coordination (#27) before this market opens up. |

**Combined Tier 3 market: ~245,000-330,000 firms.**

### Realistic ARR Trajectory

| Year | Market Focus | Customers | Avg MRR | ARR |
|---|---|---|---|---|
| **Year 1** | Elevator only | 30-50 | $130 | $47K-$78K |
| **Year 2** | Elevator + Tier 1 (fire protection, low-voltage, solar) | 150-300 | $140 | $252K-$504K |
| **Year 3** | + Tier 2 (electrical, HVAC, glazing, roofing) | 600-1,200 | $160 | $1.2M-$2.3M |
| **Year 4** | Full Tier 1+2 penetration, early Tier 3 | 2,000-4,000 | $180 | $4.3M-$8.6M |
| **Year 5** | All tiers, platform maturity | 5,000-8,000 | $200 | $12M-$19M |

These are conservative estimates assuming organic growth with a small sales team. With venture funding and an aggressive sales motion, the upper bound could be 2-3x higher.

---

## Exit Strategy & Defensibility

### "Can't Someone Just Build This? You Did It in a Month for $20."

This is the right question to ask, and the honest answer has layers:

**What's easy to replicate:**
- A chatbot that talks to a database (any dev can wire Claude to Supabase in a weekend)
- A Gantt chart (Plotly, D3, or a dozen open-source libraries)
- Basic CRUD for personnel, projects, assignments
- Voice input (Web Speech API is free)

**What's hard to replicate:**
- **Domain-tuned AI behavior.** The system prompt, tool definitions, and constraint logic that make the AI schedule like an experienced ops manager -- not just move blocks around. This is months of iteration with real users, not a weekend project. Every edge case (overlapping assignments, fractional days, cascading schedules, priority accounts, business-day logic) required specific engineering.
- **The feedback loop.** Once customers use RelAI, every scheduling decision, every correction, every "no, move that back" becomes training signal. A competitor starting from scratch doesn't have this data.
- **Industry packs.** Knowing that elevator modernizations in pre-war buildings take 20% longer, or that sprinkler fitters and elevator mechanics have different scheduling patterns -- this domain knowledge takes years to accumulate and encode.
- **Customer switching costs.** Once an ops manager's schedule, contracts, and project history live in RelAI, moving is painful. Not because of lock-in tricks, but because the AI has learned their patterns.

**The real moat isn't the code. It's the compounding intelligence:**
```
Month 1:   AI schedules like a generic assistant
Month 6:   AI schedules like a junior ops coordinator
Month 18:  AI schedules like a senior ops manager who knows your crew
Month 36:  AI schedules better than any human because it has
           pattern-matched across 1,000 similar companies
```

A competitor can clone the code. They can't clone 36 months of accumulated scheduling intelligence across hundreds of customers.

### Who Would Acquire RelAI?

#### Most Likely: ServiceTitan (NASD: TTAN)

- **Why:** They IPO'd at ~$8.9B (Dec 2024) and are actively expanding beyond home services into commercial construction. RelAI fills their biggest gap: project-based scheduling for specialty trades. Their Atlas AI is query-focused; RelAI's AI actually schedules. Acquiring is faster than building.
- **When:** Once RelAI has $5-15M ARR and proven multi-trade traction.
- **Price range:** 9-12x ARR = $45M-$180M depending on growth rate.

#### Strong Possibility: Procore (NASD: PCOR)

- **Why:** ~$1B revenue, focused on GCs and owners, but weak on specialty trade scheduling. RelAI would give them a downmarket product for the subs that use Procore's platform. They've acquired Levelset ($500M), Unearth, Intelliwave, Datagrid.
- **When:** Once RelAI demonstrates GC-sub coordination features.
- **Price range:** Similar multiples, potentially higher given strategic fit.

#### Very Likely: Constellation Software (TSX: CSU)

- **Why:** The world's most prolific vertical SaaS acquirer (134 deals in 2022 alone, $1.9B deployed in 2023). They specifically target mission-critical vertical software with $5-50M revenue and high retention. RelAI at $10M+ ARR with 90%+ retention is their ideal profile.
- **When:** Once RelAI is profitable or near-profitable with strong retention metrics.
- **Price range:** 4-7x ARR (they pay less but offer operational stability and buy-and-hold forever).

#### Other Potential Acquirers

| Acquirer | Type | Why |
|---|---|---|
| **Trimble (TRMB)** | Public | Active construction tech acquirer (Flashtract 2024, Ryvit 2023). Focused on connecting field and office. |
| **Autodesk (ADSK)** | Public | Owns PlanGrid and BuildingConnected. Would fill their gap in field scheduling. |
| **simPRO** | Private/PE-backed | Building a field service platform through acquisitions (ClockShark 2022, BigChange 2024). Direct competitor roll-up play. |
| **Bain Capital** | PE | Backed Buildertrend. Actively investing in construction tech. |
| **Accel-KKR** | PE | 46 acquisitions, active in field service and SMB software. |
| **Mainsail Partners** | PE | Invested in Arborgold (landscaping SaaS) -- directly comparable vertical trade software. |

### Comparable Exit Valuations

| Company | Revenue at Event | Valuation | Multiple | Event |
|---|---|---|---|---|
| ServiceTitan | $685M TTM | $8.9B | ~12x | IPO (Dec 2024) |
| Procore | ~$400M | $8.3B | ~20x | IPO (May 2021) |
| Levelset (→ Procore) | ~$50M est. | $500M | ~10x | Acquisition (2021) |
| Jobber | $167M | ~$400-600M est. | ~3-4x | Private (Series D) |
| Housecall Pro | ~$80-100M est. | ~$300-500M | ~4-5x | Private (Series D) |
| ClockShark (→ simPRO) | ~$10-15M est. | Undisclosed | Est. 5-8x | Acquisition (2022) |

**Median construction tech M&A multiple since 2022: 9.1x LTM ARR.**

### How to Position for Acquisition

The playbook is straightforward:

1. **Prove the AI moat is real.** Show that scheduling accuracy improves over time with usage data. Publish case studies showing time savings (e.g., "Ops manager went from 2 hours/day scheduling to 15 minutes").

2. **Demonstrate multi-trade expansion.** An elevator-only tool is a niche acquisition ($5-20M). A multi-trade platform is a strategic acquisition ($50-200M+). Each new trade you enter increases the multiple.

3. **Hit retention benchmarks.** Construction SaaS acquirers care about:
   - Net Revenue Retention > 110% (customers expand over time)
   - Logo retention > 90% (customers don't churn)
   - These metrics prove switching costs are real

4. **Stay capital-efficient.** Constellation Software and PE acquirers pay premiums for businesses that don't burn cash. Being built in a month for $20 is a strength, not a weakness -- it means the unit economics are exceptional.

5. **Build where acquirers are weak.** ServiceTitan can't do project scheduling. Procore can't do small-company AI. Trimble can't do conversational interfaces. Each gap you fill makes you more attractive to that specific buyer.

### The "Don't Sell" Scenario

If the market plays out at the upper end and RelAI reaches $20M+ ARR with strong growth, an IPO or long-term independent operation becomes viable. The construction tech sector averaged 37% valuation increases since 2020, and the labor shortage is a secular tailwind that makes crew scheduling software more valuable every year. At $50M ARR with 80%+ gross margins, RelAI would be valued at $450-600M as a standalone business.
