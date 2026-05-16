import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Create deeply-nested distractor directory structure ──────────────────────
dirs = [
    "workspace/clients/vip_tier1/2024_trips",
    "workspace/clients/vip_tier1/2023_trips",
    "workspace/clients/vip_tier2/pending",
    "workspace/clients/vip_tier2/archived",
    "workspace/templates/internal",
    "workspace/templates/deprecated",
    "workspace/vendor_contracts/flights",
    "workspace/vendor_contracts/hotels",
    "workspace/vendor_contracts/experiences",
    "workspace/finance/invoices/2024",
    "workspace/finance/budgets/approved",
    "workspace/ops/scripts",
    "workspace/ops/logs",
    "workspace/marketing/brochures",
    "workspace/itineraries/drafts",
    "workspace/itineraries/published",
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# ── Distractor files (messy, realistic) ──────────────────────────────────────

# 1. Old client trip brief (different client, different destination)
Path("workspace/clients/vip_tier1/2023_trips/hong_kong_brief.txt").write_text(
    """Client: Wang Fang
Destination: Hong Kong
Dates: 2023-11-10 to 2023-11-14
Budget: ~¥500,000
Notes: Wants Peninsula Hotel, Rolls Royce transfer, dim sum experience.
Status: COMPLETED
""")

# 2. Deprecated template (wrong format, old version)
Path("workspace/templates/deprecated/old_luxury_template.md").write_text(
    """# OLD TEMPLATE - DO NOT USE

## Trip Overview
[Client Name]
[Destination]
[Budget]

## Flights
[Airline] [Class]

## Hotels
[Hotel Name]

## Total Cost: [Amount]

NOTE: This template was deprecated in Q3 2023. Use the new concierge template.
""")

# 3. Vendor contract snippet (flights)
Path("workspace/vendor_contracts/flights/emirates_sla_2024.txt").write_text(
    """Emirates Airlines - Corporate SLA Agreement 2024
Preferred rates for Business Class: -8% off published fares
First Class availability: subject to inventory
Contact: groups@emirates-corporate.com
Min booking lead time: 21 days
Special amenity requests: 48h notice required
""")

# 4. Finance budget template (partial, unrelated)
Path("workspace/finance/budgets/approved/q4_2024_budget.json").write_text(
    json.dumps({
        "department": "luxury_travel_division",
        "q4_budget": 50000000,
        "categories": {
            "flights": 20000000,
            "hotels": 15000000,
            "experiences": 10000000,
            "ops": 5000000
        },
        "approved_by": "CFO",
        "date": "2024-10-01"
    }, indent=2, ensure_ascii=False)
)

# 5. Internal ops script (mock, unrelated)
Path("workspace/ops/scripts/daily_sync.sh").write_text(
    """#!/bin/bash
# Daily sync script - DO NOT EDIT
rsync -avz /data/bookings/ /backup/bookings/
echo "Sync complete: $(date)"
""")

# 6. Old invoice
Path("workspace/finance/invoices/2024/INV-2024-0312.txt").write_text(
    """Invoice #2024-0312
Client: Zhang Wei
Service: Maldives Luxury Package
Amount: ¥1,230,000
Status: PAID
Date: 2024-03-12
""")

# 7. Hotel vendor notes
Path("workspace/vendor_contracts/hotels/aman_preferred_rates.txt").write_text(
    """Aman Hotels - Preferred Partner Agreement
Complimentary upgrade: subject to availability
Late checkout: guaranteed to 4PM
Rate code: LUXURY2024
Minimum stay: 3 nights peak season
Contact: reservations@aman.com
""")

# 8. Marketing brochure draft
Path("workspace/marketing/brochures/new_zealand_draft.txt").write_text(
    """NEW ZEALAND LUXURY ESCAPE - DRAFT BROCHURE
Pristine wilderness meets unparalleled luxury.
Helicopter glacier walks, private vineyard tours,
milford sound yacht charters...
[IMAGES NEEDED]
[PRICING TBD]
Status: DRAFT - not for distribution
""")

# 9. Log file (noise)
Path("workspace/ops/logs/system.log").write_text(
    """2024-12-01 09:00:01 INFO  System started
2024-12-01 09:00:05 INFO  Database connection established
2024-12-01 09:15:22 WARN  API timeout for booking reference BK-4421
2024-12-01 10:30:00 INFO  Backup completed successfully
2024-12-01 14:22:11 ERROR Vendor API rate limit reached: retrying in 60s
""")

# 10. Draft itinerary (different destination, incomplete)
Path("workspace/itineraries/drafts/kenya_safari_v1.md").write_text(
    """# Kenya Safari Draft - INCOMPLETE

## Client: TBD
## Dates: March 2025

### Day 1
- Arrive Nairobi
- Transfer to Masai Mara (TBD: helicopter or road?)
- Check in: andBeyond Bateleur Camp

### Day 2
- Morning game drive
- [EXPERIENCE TBD]

### Budget: TBD
*Status: needs client approval*
""")

# 11. Published itinerary sample (Maldives, different format)
Path("workspace/itineraries/published/maldives_chen_2024.txt").write_text(
    """PUBLISHED ITINERARY - Chen Family - Maldives 2024
Hotel: One&Only Reethi Rah - Overwater Villa
Flights: Cathay Pacific Business + Seaplane
Activities: Snorkeling, Sunset Cruise, SPA
Total: ¥890,000 (4pax, 7 nights)
Status: DELIVERED
""")

# 12. Competitor analysis notes
Path("workspace/clients/vip_tier2/archived/competitor_notes.txt").write_text(
    """Competitor Analysis - Q2 2024
Main competitors: Cox & Kings, Kuoni, Scott Dunn
Our differentiators:
- Chinese language concierge 24/7
- Private jet partnerships (VistaJet, NetJets)
- Faster response times
- Better Aman/Four Seasons relationships
""")

# ── THE ACTUAL TASK INPUT: Client brief ──────────────────────────────────────
# This is the raw client request the agent must process
Path("workspace/clients/vip_tier1/2024_trips/client_brief_li_jun.txt").write_text(
    """CLIENT BRIEF - Li Jun & Partner (2 persons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Received: 2025-07-15
Account Manager: [UNASSIGNED]

TRIP DETAILS
────────────
Destination:    New Zealand (South Island focus)
Dates:          2025-09-01 to 2025-09-08  (8 days, 7 nights)
Travelers:      2 persons (couple, anniversary trip)
Occasion:       10th Wedding Anniversary
Budget:         OPEN - deliver the BEST, not just the most expensive
Theme:          Nature + Wilderness + Luxury

CLIENT PREFERENCES
──────────────────
- Loves flying experiences (helicopters, scenic flights)
- Interested in wine/gastronomy (private vineyard preferred)
- Wants at least one superyacht/charter boat experience
- Hates crowds - maximum privacy
- Prefers English+Chinese bilingual service where possible

FLIGHT PREFERENCES
──────────────────
- Departing from: Shanghai (PVG)
- Open to premium airlines - client has flown Singapore Airlines before
- Wants best available option (no budget constraint)

ACCOMMODATION
─────────────
- Must be luxury/ultra-luxury brand
- Interested in unique experiences (not just generic 5-star)
- Private villa or exclusive suite preferred

SPECIFIC MUST-HAVES (client mentioned explicitly)
──────────────────────────────────────────────────
1. Helicopter glacier experience (Fox Glacier or Franz Josef)
2. Private wine tasting in Marlborough or Central Otago
3. Milford Sound or Doubtful Sound boat charter
4. Supercar self-drive on South Island roads

DELIVERABLE
────────────
Please produce a complete luxury travel dossier for this client.
Save the final plan as: nz_luxury_plan_li_jun.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

print("Workspace initialized successfully.")
print(f"Client brief: workspace/clients/vip_tier1/2024_trips/client_brief_li_jun.txt")
print(f"Total distractor files created: 12")