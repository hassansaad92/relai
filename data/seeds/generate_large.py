#!/usr/bin/env python3
"""Generate large seed dataset with ~50 mechanics, ~100 projects, and realistic
assignment timing conflicts (gaps and overlaps)."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

OUT = Path(__file__).parent / "large"

# ── Skills ────────────────────────────────────────────────────────────────────
SKILLS = ["Gen2", "Geared", "Gearless", "Compass", "Machine Replacement"]

# ── Personnel (50 mechanics) ─────────────────────────────────────────────────
FIRST_NAMES = [
    "James", "Mary", "Robert", "Linda", "Michael", "Barbara", "David", "Susan",
    "William", "Jessica", "Richard", "Sarah", "Joseph", "Karen", "Thomas",
    "Lisa", "Charles", "Nancy", "Daniel", "Betty", "Matthew", "Dorothy",
    "Anthony", "Sandra", "Mark", "Ashley", "Donald", "Kimberly", "Steven",
    "Emily", "Paul", "Donna", "Andrew", "Michelle", "Joshua", "Carol",
    "Kenneth", "Amanda", "Kevin", "Melissa", "Brian", "Deborah", "George",
    "Stephanie", "Timothy", "Rebecca", "Ronald", "Sharon", "Edward", "Laura",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts",
]

# Skill distribution: most mechanics have 1-2 skills
def random_skills():
    n = random.choices([1, 2, 3], weights=[50, 40, 10])[0]
    return ",".join(random.sample(SKILLS, n))

personnel = []
for i in range(1, 51):
    name = f"{FIRST_NAMES[i-1]} {LAST_NAMES[i-1]}"
    skills = random_skills()
    personnel.append({"id": i, "name": name, "skills": skills})

# ── Projects (100 projects) ──────────────────────────────────────────────────
PREFIXES = [
    "Downtown", "Elmwood", "Riverside", "Maplewood", "Grand", "Birchwood",
    "Brookside", "Creekside", "Hillcrest", "Thornfield", "Westfield",
    "Parkview", "Pinecrest", "Silverton", "Gateway", "Clearwater", "Highland",
    "Midtown", "Pinehurst", "Eastside", "Willowbrook", "Stonegate", "Bayside",
    "Harborview", "Fairview", "Lakeside", "Copperfield", "Northgate",
    "Cedarwood", "Ridgeline", "Kingsbridge", "Metropolitan", "Meadowbrook",
    "Oceanview", "Greenfield", "Sunset", "Lincoln", "Pyramid",
]
SUFFIXES = [
    "Stadium", "Corporate Center", "City Hall", "Shopping Plaza", "Hotel",
    "Residences", "Convention Center", "Hospital", "High School", "Museum",
    "Medical Center", "Office Tower", "Condominiums", "Tech Campus",
    "Library", "Luxury Tower", "University Hall", "Apartments", "Tower",
]

SKILL_COMBOS = [
    "Gen2", "Geared", "Gearless", "Compass", "Machine Replacement",
    "Gen2,Geared", "Gen2,Gearless", "Gen2,Compass", "Gen2,Machine Replacement",
    "Geared,Compass", "Geared,Machine Replacement", "Gearless,Compass",
    "Gearless,Machine Replacement",
    "Gen2,Geared,Compass",
]

used_names = set()
projects = []
base_date = date(2025, 12, 1)

for i in range(1, 101):
    # Generate unique project name
    while True:
        name = f"{random.choice(PREFIXES)} {random.choice(SUFFIXES)}"
        if name not in used_names:
            used_names.add(name)
            break

    # Spread projects: weight heavily toward past/near-future so most are "active"
    # 80% start within first 5 months (before today), 20% further out
    if random.random() < 0.80:
        start_offset = random.randint(0, 120)  # Dec 2025 – Mar 2026
    else:
        start_offset = random.randint(120, 400)  # Apr 2026 – Jan 2027
    req_start = base_date + timedelta(days=start_offset)
    # Monday-align
    req_start -= timedelta(days=req_start.weekday())

    # ~15% are prep/touchup jobs (0 elevators, 1-2 weeks)
    if random.random() < 0.15:
        num_elevators = 0
        required_skills = ""
        duration_weeks = random.choice([1, 2])
        suffix = random.choice(["Prep", "Touchup"])
        # Override name to reflect job type
        while True:
            name = f"{random.choice(PREFIXES)} {suffix}"
            if name not in used_names:
                used_names.add(name)
                break
    else:
        num_elevators = random.randint(1, 8)
        required_skills = random.choice(SKILL_COMBOS)
        duration_weeks = 10 * num_elevators

    req_end = req_start + timedelta(weeks=duration_weeks)

    # First 60 awarded, next 40 pending
    award_status = "awarded" if i <= 60 else "pending_award"

    projects.append({
        "id": i,
        "name": name,
        "committed_start_date": req_start.isoformat(),
        "committed_end_date": req_end.isoformat(),
        "duration_days": duration_weeks * 7,
        "num_elevators": num_elevators,
        "required_skills": required_skills,
        "award_status": award_status,
        "procurement_date": "",
    })

# ── Assignments (with realistic gaps/overlaps) ──────────────────────────────
# Strategy: assign each mechanic a current project, then pick a "next" project
# whose requested_start is NEAR (but not exactly at) the current assignment end.
# The delta between current_end and next_requested_start creates the conflict:
#   positive delta = mechanic finishes AFTER next project wants to start (delay!)
#   negative delta = mechanic finishes BEFORE (idle gap)

assignments = []
aid = 1
today = date(2026, 3, 10)

# Sort awarded projects by requested_start for realistic scheduling
awarded_projects = sorted(
    [p for p in projects if p["award_status"] == "awarded"],
    key=lambda p: p["committed_start_date"],
)

# Split into "current" (can be active today) and "future" pools
# Current: projects with requested_start up to 4 weeks after today (already begun)
current_cutoff = today + timedelta(weeks=4)
current_pool = [p for p in awarded_projects
                if date.fromisoformat(p["committed_start_date"]) <= current_cutoff]
future_pool = [p for p in awarded_projects
               if date.fromisoformat(p["committed_start_date"]) > current_cutoff]
random.shuffle(current_pool)
random.shuffle(future_pool)

assigned_project_ids = set()

# Leave 3 mechanics unassigned (no current project)
unassigned_indices = random.sample(range(len(personnel)), 3)
unassigned_ids = {personnel[i]["id"] for i in unassigned_indices}

for person in personnel:
    if person["id"] in unassigned_ids:
        continue  # skip — these mechanics have no work
    if not current_pool:
        break

    # ── Current assignment (active today) ──
    proj1 = current_pool.pop(0)
    assigned_project_ids.add(proj1["id"])
    p1_start = date.fromisoformat(proj1["committed_start_date"])
    duration = timedelta(days=proj1["duration_days"])

    # Assignment start: near project requested start ± a few days
    assign1_start = p1_start + timedelta(days=random.randint(-7, 14))

    # Assignment end: start + project duration ± small variance (up to ±2 weeks)
    duration_shift = timedelta(days=random.randint(-10, 14))
    assign1_end = assign1_start + duration + duration_shift

    # If this project already finished before today, skip it — pick next
    if assign1_end <= today:
        continue

    assignments.append({
        "id": aid,
        "personnel_id": person["id"],
        "project_id": proj1["id"],
        "sequence": 1,
        "start_date": assign1_start.isoformat(),
        "end_date": assign1_end.isoformat(),
        "assignment_type": "full",
        "allocated_days": 1.0,
    })
    aid += 1

    # ── Next assignment for ~70% of mechanics ──
    # Only if there's a project whose requested_start is realistically near
    # this mechanic's completion (within ~90 days). This creates natural
    # gaps (-30d) and overlaps (+60d) without absurd 300-day deltas.
    if future_pool and random.random() < 0.7:
        candidates = [
            p for p in future_pool
            if -30 <= (assign1_end - date.fromisoformat(p["committed_start_date"])).days <= 60
        ]
        if candidates:
            proj2 = random.choice(candidates)
            future_pool.remove(proj2)
            assigned_project_ids.add(proj2["id"])

            p2_req_start = date.fromisoformat(proj2["committed_start_date"])

            # Assignment starts when mechanic is available (current end + small buffer)
            buffer_days = random.randint(-5, 10)
            assign2_start = assign1_end + timedelta(days=buffer_days)

            # Duration matches project duration ± small variance
            assign2_end = assign2_start + timedelta(days=proj2["duration_days"]) + timedelta(days=random.randint(-10, 14))

            assignments.append({
                "id": aid,
                "personnel_id": person["id"],
                "project_id": proj2["id"],
                "sequence": 2,
                "start_date": assign2_start.isoformat(),
                "end_date": assign2_end.isoformat(),
                "assignment_type": "full",
                "allocated_days": 1.0,
            })
            aid += 1

# Some large projects need multiple mechanics
remaining = [p for p in awarded_projects
             if p["num_elevators"] >= 5 and p["id"] not in assigned_project_ids]
extra_personnel = list(personnel)
random.shuffle(extra_personnel)
random.shuffle(remaining)

for proj in remaining[:10]:
    if not extra_personnel:
        break
    person = extra_personnel.pop(0)
    p_start = date.fromisoformat(proj["committed_start_date"])
    p_end = date.fromisoformat(proj["committed_end_date"])

    assign_start = p_start + timedelta(days=random.randint(-7, 14))
    assign_end = assign_start + timedelta(days=proj["duration_days"]) + timedelta(days=random.randint(-10, 14))

    assignments.append({
        "id": aid,
        "personnel_id": person["id"],
        "project_id": proj["id"],
        "sequence": 1,
        "start_date": assign_start.isoformat(),
        "end_date": assign_end.isoformat(),
        "assignment_type": "full",
        "allocated_days": 1.0,
    })
    aid += 1

# ── Write CSVs ───────────────────────────────────────────────────────────────
OUT.mkdir(parents=True, exist_ok=True)

with open(OUT / "skills.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["skill"])
    for s in SKILLS:
        w.writerow([s])

with open(OUT / "personnel.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["id", "name", "skills"])
    w.writeheader()
    w.writerows(personnel)

with open(OUT / "projects.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[
        "id", "name", "committed_start_date", "committed_end_date",
        "duration_days", "num_elevators", "required_skills", "award_status",
        "procurement_date",
    ])
    w.writeheader()
    w.writerows(projects)

with open(OUT / "assignments.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=[
        "id", "personnel_id", "project_id", "sequence",
        "start_date", "end_date", "assignment_type", "allocated_days",
    ])
    w.writeheader()
    w.writerows(assignments)

# Print summary
seq1 = [a for a in assignments if a["sequence"] == 1]
seq2 = [a for a in assignments if a["sequence"] == 2]
print(f"Personnel:    {len(personnel)} ({len(unassigned_ids)} unassigned)")
print(f"Projects:     {len(projects)}")
print(f"Assignments:  {len(assignments)} ({len(seq1)} current, {len(seq2)} next)")

# Show conflict examples: current_end vs next_project_requested_start
print("\nSample gaps/overlaps (current_end → next_project_requested_start):")
for a2 in seq2[:8]:
    proj2 = next(p for p in projects if p["id"] == a2["project_id"])
    # Find this person's current assignment
    a1 = next((a for a in seq1 if a["personnel_id"] == a2["personnel_id"]), None)
    if a1:
        current_end = date.fromisoformat(a1["end_date"])
        req_start = date.fromisoformat(proj2["committed_start_date"])
        delta = (current_end - req_start).days
        person_name = next(p["name"] for p in personnel if p["id"] == a2["personnel_id"])
        label = f"+{delta}d LATE" if delta > 0 else f"{delta}d gap" if delta < 0 else "exact"
        print(f"  {person_name}: finishes {a1['end_date']}, "
              f"next wants {proj2['committed_start_date']} ({label})")
