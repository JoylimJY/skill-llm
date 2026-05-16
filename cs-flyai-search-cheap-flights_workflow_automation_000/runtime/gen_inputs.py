import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Create a deeply nested distractor structure ──────────────────────────────

dirs = [
    "ops/travel/2025",
    "ops/travel/2024/archive",
    "ops/expenses/q1",
    "ops/expenses/q2",
    "hr/onboarding",
    "hr/offsite_planning",
    "finance/budgets",
    "finance/reports",
    "projects/alpha/docs",
    "projects/beta/specs",
    "infra/configs",
    "infra/scripts",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "ops/travel/2025/hotel_bookings.csv": (
        "id,city,hotel,checkin,checkout,price\n"
        "1,Sanya,Atlantis,2025-11-10,2025-11-13,1200\n"
        "2,Chengdu,Sheraton,2025-10-05,2025-10-07,850\n"
    ),
    "ops/travel/2024/archive/old_flight_prices.txt": (
        "Chengdu->Sanya  2024-03-10  Spring Airlines  ¥450\n"
        "Chengdu->Sanya  2024-03-12  China Southern   ¥520\n"
        "NOTE: Prices are from 2024 and may not be current.\n"
    ),
    "ops/expenses/q1/team_offsite_budget.json": json.dumps({
        "event": "Q1 Team Offsite",
        "destination": "Sanya",
        "headcount": 8,
        "flight_budget_per_person_cny": 1200,
        "hotel_budget_per_person_per_night_cny": 600,
        "dates": {"start": "2025-11-10", "end": "2025-11-14"}
    }, indent=2, ensure_ascii=False),
    "ops/expenses/q2/summary.csv": (
        "category,amount_cny\nflights,9600\nhotels,14400\nmeals,3200\n"
    ),
    "hr/offsite_planning/attendees.txt": (
        "Alice Wang\nBob Zhang\nCarol Liu\nDavid Chen\nEva Huang\nFrank Zhou\nGrace Li\nHenry Wu\n"
    ),
    "hr/onboarding/travel_policy.txt": (
        "Travel Policy v3.2\n"
        "- Economy class only for domestic flights\n"
        "- Book at least 7 days in advance\n"
        "- Maximum flight budget: ¥1200 per person one-way\n"
        "- Preferred airlines: Air China, China Southern, China Eastern\n"
        "- All bookings must include booking confirmation URL\n"
    ),
    "finance/budgets/2025_offsite.xlsx.stub": "Binary Excel stub - use finance portal to view",
    "finance/reports/q3_travel_expenses.txt": (
        "Q3 Travel Expenses Report\nTotal: ¥45,230\nFlights: ¥18,400\nAccommodation: ¥22,100\nOther: ¥4,730\n"
    ),
    "projects/alpha/docs/kickoff_notes.md": (
        "# Alpha Kickoff Notes\n- Team offsite planned for November in Sanya\n"
        "- Need to book flights from Chengdu\n- Budget cap ¥1200/person\n"
    ),
    "projects/beta/specs/requirements.txt": (
        "Feature: Travel search integration\nPriority: Low\nOwner: Ops team\n"
    ),
    "infra/configs/app.json": json.dumps({
        "app": "ops-portal",
        "version": "1.4.2",
        "features": {"travel_search": False, "expense_tracking": True}
    }, indent=2),
    "infra/scripts/deploy.sh": (
        "#!/bin/bash\necho 'Deploying ops-portal v1.4.2'\n# TODO: add flight search module\n"
    ),
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content, encoding="utf-8")

# ── Task brief (the actual job spec for the agent) ───────────────────────────
task_brief = """# Team Offsite Flight Search Brief

**Requestor:** Grace Li, Operations Manager  
**Date:** 2025-10-20  
**Destination:** Sanya  
**Origin:** Chengdu  
**Flexible Departure Window:** 2025-11-08 to 2025-11-14  
**Budget Cap:** ¥1,200 per person (one-way, economy)  
**Headcount:** 8 staff  
**Notes:**
- Need the cheapest available options sorted by price
- Staff are flexible on timing — red-eye or connecting flights are acceptable
- All results must include clickable booking links
- Save the final search report to: flight_report.md
"""
(workspace / "ops/travel/2025/task_brief.txt").write_text(task_brief, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 1}")