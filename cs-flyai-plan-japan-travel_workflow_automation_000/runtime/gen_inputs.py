import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create deeply nested distractor files ---
dirs = [
    "company/hr/travel_policies",
    "company/hr/visa_documents",
    "company/finance/budgets/2026",
    "company/it/tools",
    "company/ops/logs",
    "projects/japan_initiative/drafts",
    "projects/japan_initiative/old_plans",
    "projects/southeast_asia/cancelled",
    "references/internal",
    "references/external",
    "tmp/cache",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor 1: old travel policy PDF stub
with open(os.path.join(workspace, "company/hr/travel_policies/travel_policy_2024.txt"), "w") as f:
    f.write("Travel Policy 2024 - OUTDATED\nAll flights must be economy. Max hotel: ¥1200/night.\nVisa handling: employee responsible.\n")

# Distractor 2: partial visa notes
with open(os.path.join(workspace, "company/hr/visa_documents/japan_visa_notes_2023.txt"), "w") as f:
    f.write("Japan visa - single entry. Requires: passport, bank statement, itinerary.\n[OUTDATED - do not use for 2026 planning]\n")

# Distractor 3: budget spreadsheet stub
with open(os.path.join(workspace, "company/finance/budgets/2026/japan_trip_budget_DRAFT.csv"), "w") as f:
    f.write("Category,Estimated Cost (CNY)\nFlights,5000\nHotels,4000\nAttractions,800\nFood,1200\nInsurance,300\n")

# Distractor 4: old itinerary draft (deliberately wrong format, no booking links)
with open(os.path.join(workspace, "projects/japan_initiative/old_plans/itinerary_draft_v1.md"), "w") as f:
    f.write("""# Japan Trip Draft v1 (DO NOT USE)
Day 1: Tokyo - Arrive at Narita
Day 2: Tokyo - Visit Senso-ji Temple
Day 3: Osaka - Dotonbori
NOTE: This draft has no prices or booking links. Needs update.
""")

# Distractor 5: generic asia travel notes
with open(os.path.join(workspace, "projects/southeast_asia/cancelled/SEA_notes.txt"), "w") as f:
    f.write("Southeast Asia trip cancelled Q3 2026. Budget reallocated to Japan.\n")

# Distractor 6: IT tools config
with open(os.path.join(workspace, "company/it/tools/npm_registry.txt"), "w") as f:
    f.write("Internal npm registry: http://npm.internal.company.com (offline)\nFallback: https://registry.npmjs.org\n")

# Distractor 7: ops log
with open(os.path.join(workspace, "company/ops/logs/travel_requests_2026.log"), "w") as f:
    f.write("2026-01-10 | Employee: Zhang Wei | Destination: Tokyo | Status: PENDING\n2026-01-12 | Employee: Li Mei | Destination: Osaka | Status: APPROVED\n")

# Distractor 8: references - internal note
with open(os.path.join(workspace, "references/internal/japan_contacts.txt"), "w") as f:
    f.write("Tokyo Office Contact: Tanaka-san +81-3-XXXX-XXXX\nOsaka Partner: Yamamoto Corp\n")

# Distractor 9: external reference (fake JR Pass prices - stale)
with open(os.path.join(workspace, "references/external/jr_pass_2024_prices.txt"), "w") as f:
    f.write("JR Pass 7-day: ¥50,000 JPY (2024 price - MAY BE OUTDATED)\nJR Pass 14-day: ¥80,000 JPY\n")

# Distractor 10: tmp cache
with open(os.path.join(workspace, "tmp/cache/last_flight_search.json"), "w") as f:
    json.dump({"status": "expired", "cache_date": "2025-01-01", "data": []}, f)

# Distractor 11: a confusingly named partial file
with open(os.path.join(workspace, "projects/japan_initiative/drafts/itinerary_template_BROKEN.md"), "w") as f:
    f.write("""## Japan Trip Template (BROKEN - missing data)
### Day N · {City} — {Theme}
🏨 **Hotel:** {name} ¥{price}/night · [Book]()   <- URL MISSING
NOTE: Do not submit this file. Generate a proper one.
""")

# --- The actual task input brief ---
# This is the "request" the agent must fulfill
with open(os.path.join(workspace, "projects/japan_initiative/trip_request_brief.txt"), "w") as f:
    f.write("""JAPAN TRIP PLANNING REQUEST
===========================
Requestor: HR Department
Date: 2026-04-20
Employee: Zhang Wei (Business + Leisure)

Trip Details:
- Departure City: Beijing
- Outbound: 2026-05-10 (Beijing → Tokyo)
- Cities to Visit: Tokyo (2 nights), Osaka (2 nights)
- Return: 2026-05-14 (Osaka → Beijing)
- Interests: Temples/shrines in Kyoto, food markets in Osaka, top attractions in Tokyo
- Budget: Standard (no luxury filter needed)

Deliverable:
Please produce a complete, ready-to-submit travel itinerary document named: japan_itinerary_zhangwei.md

The document must include:
1. Visa information
2. Outbound and return flights with booking links
3. Hotel recommendations for Tokyo and Osaka with booking links
4. Attraction suggestions for Tokyo (top-rated), Osaka (food markets), and temple/shrine POIs
5. Day-by-day schedule
6. Must be usable by HR for final submission

IMPORTANT: Use only real-time data from the official travel tool. Do not use any outdated data from our internal drafts.
""")

print("Workspace setup complete.")
print(f"Files created in {workspace}")