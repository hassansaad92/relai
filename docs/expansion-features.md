# RelAI: Custom AI Operations Platform

## Business Model: Custom-Build Consulting

RelAI is a custom AI-powered operations platform built per-company. Instead of shipping a one-size-fits-all SaaS product, we build tailored scheduling and operations systems for individual construction and elevator companies using AI-accelerated development ("vibe coding").

### Why Custom, Not SaaS

The vibe-coding ecosystem has made it trivially easy to spin up CRUD apps with AI chatbots. A SaaS scheduling tool no longer has a defensible moat -- anyone can build a basic version in a weekend. What's hard to replicate is **domain-tuned, company-specific operational logic** built through direct collaboration with an ops manager over weeks, not months.

**The pitch:** "I'll build you a custom AI scheduling system tailored to how your company actually works -- in 2 months, for a fraction of what ServiceTitan costs, with none of the 6-month implementation headaches."

### How It Works

1. **Engagement**: A company pays for ~2 months of dedicated development time
2. **Discovery**: Work directly with the ops manager to understand their workflows, constraints, and pain points
3. **Build**: Use the RelAI base platform as a starting point, then customize the data model, AI behavior, UI, and integrations for their specific operation
4. **Deploy**: Simple infrastructure (Supabase + a single server) -- no Kubernetes, no over-engineering. Hosting costs stay under $50/month
5. **Handoff + Support**: Ongoing maintenance retainer or ad-hoc support as needed

### Unit Economics

| Component | Estimate |
|---|---|
| Engagement fee (2 months) | $15,000-$25,000 |
| Monthly hosting cost | $25-50 |
| Monthly AI API cost | $10-30 |
| Ongoing support retainer (optional) | $500-$1,500/mo |

Compare to ServiceTitan: $30,000-$60,000/year for a 10-person shop, with a 6-month implementation. We deliver faster, cheaper, and more tailored.

### Scaling the Model

| Phase | Focus | Revenue Target |
|---|---|---|
| **Phase 1** | Star Elevator (first customer, prove the model) | $15-25K |
| **Phase 2** | 3-5 elevator companies using the base platform with per-company customization | $60-125K |
| **Phase 3** | Expand to adjacent trades (fire protection, low-voltage, solar) | $150-300K |
| **Phase 4** | Hire junior developers, systematize the customization process | $500K+ |

Each engagement makes the base platform more capable. Features built for one company often apply (with tweaks) to the next. Over time, the base platform matures enough that new engagements take less time while commanding similar fees.

---

## Current Platform: Star Elevator MVP

### What Exists Today

- **AI Scheduling Engine**: Claude-powered chatbot that creates, modifies, and reasons about schedules through natural language
- **Gantt Chart Overview**: Visual timeline of all crew assignments across projects (Plotly.js)
- **Personnel Management**: Skill tracking with availability derived from assignments
- **Project Management**: Committed/actual dates, fractional durations, procurement tracking
- **Assignment System**: Three types (full, cascading, partial), fractional-day support, business-day logic
- **Scenario Versioning**: Master/draft workflow for what-if schedule planning
- **Spreadsheet Upload**: Bulk project import from Excel with duration calculation

### Star Elevator Customization Priorities

These are the features to build out for the first customer engagement:

1. **Risk Badges & Alerts** -- Flag projects missing materials or crew assignments within a configurable window of their start date. Surface these on the schedule view so nothing falls through the cracks.

2. **Daily Dispatch** -- Generate a per-crew daily briefing: today's assignments, project addresses, special instructions. Delivered via email or a mobile-friendly web page (no app install).

3. **Procurement Tracking** -- Track material status per project with configurable statuses. Auto-derive procurement dates and flag lead-time conflicts against the schedule.

4. **Contract Document Storage** -- Upload PDF contracts per project. Start with simple storage and retrieval; add AI-powered contract Q&A (RAG) if the customer needs it.

5. **Workload Visibility** -- Dashboard showing crew utilization over a rolling window. Highlight overloaded or idle personnel.

### Features to Build Per-Customer (as needed)

Not every company needs the same thing. These are capabilities we can offer depending on the engagement:

| Feature | Description | Complexity |
|---|---|---|
| **Contract RAG** | AI answers questions about uploaded contracts using retrieval-augmented generation | Medium |
| **Sales Intake Portal** | Structured form for salespeople to submit new projects to the ops queue | Low |
| **Subcontractor Coordination** | Limited portal for subs to view scope and confirm availability | Medium |
| **BOM Generation** | Auto-generate procurement checklists from project type and contract scope | Medium |
| **Customer Status Reports** | One-click PDF reports for customers, auto-populated from schedule data | Low |
| **Notification System** | Alerts on status changes via email/SMS/Slack | Low |
| **Voice Interface** | Hands-free scheduling commands for ops managers in the field | Medium |
| **Cash Flow Forecasting** | Project revenue by month based on schedule and payment terms | High |

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend | FastAPI (Python) | Simple, fast, easy to customize per client |
| Database | Supabase (PostgreSQL) | Managed hosting, pgvector for RAG, cheap at small scale |
| AI | Anthropic Claude API | Best reasoning for scheduling logic |
| Frontend | Vanilla JS + Plotly | No framework overhead, fast iteration |

Each customer gets their own Supabase project. No multi-tenancy complexity. Deployments are simple and isolated.

---

## Historical Reference: SaaS Model

_The original plan was to build RelAI as a multi-tenant SaaS product. This section is kept for reference. The full SaaS strategy document is archived at `docs/archive/expansion-features-saas-model.md`._

### Proposed SaaS Pricing (Not Pursuing)

| Tier | Price | Target |
|---|---|---|
| Starter | $79/mo | 1-5 person shops |
| Growth | $149/mo | 6-15 person companies |
| Pro | $249/mo | 16-30 person companies |

### Why We Moved Away From SaaS

- **Low defensibility**: Vibe coding makes it easy for anyone to build a basic AI scheduling app. The "moat" of a conversational scheduling engine is no longer unique.
- **Sales and marketing overhead**: Reaching 200+ customers requires a go-to-market machine that doesn't make sense as a solo/small-team operation.
- **Support burden**: Multi-tenant SaaS requires handling diverse customer needs through configuration, not customization. This leads to feature bloat and slower iteration.
- **The custom model is more profitable sooner**: One $20K engagement beats 10 months of chasing $149/mo subscribers through a funnel.

### SaaS Market Sizing (For Reference)

- TAM: ~500,000 US specialty trade firms (1-30 employees)
- SAM: ~150,000 firms with enough complexity to benefit
- Realistic 5-year SOM: 7,500-12,000 customers at $27-43M ARR
- Elevator-only ceiling: ~$644K ARR (too small to sustain a SaaS business alone)
