import os
import random
import json
import csv

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep distractor directory structure ──────────────────────────────────────
dirs = [
    "agency/clients/vip",
    "agency/clients/corporate",
    "agency/finance/invoices/2024",
    "agency/finance/invoices/2023",
    "agency/marketing/brochures",
    "agency/marketing/social",
    "agency/ops/schedules",
    "agency/ops/vendor_contacts",
    "agency/crm/leads",
    "agency/crm/bookings/confirmed",
    "agency/crm/bookings/pending",
    "legacy/old_system/exports",
    "legacy/old_system/templates",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractor_files = {
    "agency/clients/vip/henderson_profile.txt": (
        "Client: James Henderson\nPreference: Luxury, private anchorages\nBudget: $25,000/week\nNotes: Requires chef onboard"
    ),
    "agency/clients/corporate/acme_retreat.txt": (
        "Company: Acme Corp\nEvent: Team building retreat Q3\nSize: 12 pax\nBudget TBD"
    ),
    "agency/finance/invoices/2024/INV-2024-0091.csv": (
        "invoice_id,client,amount,status\nINV-2024-0091,Henderson,24500.00,paid\nINV-2024-0092,Smith,18200.00,pending"
    ),
    "agency/finance/invoices/2023/annual_summary.json": json.dumps({
        "year": 2023, "total_revenue": 412000, "charters_booked": 34
    }, indent=2),
    "agency/marketing/brochures/bvi_highlights.txt": (
        "Top BVI destinations: The Baths on Virgin Gorda, Soggy Dollar Bar on Jost Van Dyke, "
        "The Caves at Norman Island, Pink Sand Beach on Anegada."
    ),
    "agency/marketing/social/instagram_captions.txt": (
        "Caption 1: Sun, sails, and serenity. #BVI #SailingLife\n"
        "Caption 2: Drop anchor at The Baths for a morning swim. #VirginGorda"
    ),
    "agency/ops/schedules/fleet_availability_june.csv": (
        "vessel,type,LOA_ft,cabins,available_from,available_to\n"
        "Serenity,Catamaran,45,4,2024-06-01,2024-06-30\n"
        "Blue Horizon,Monohull,52,5,2024-06-08,2024-06-28\n"
        "Island Dream,Catamaran,48,4,2024-06-15,2024-07-15"
    ),
    "agency/ops/vendor_contacts/provisioning_suppliers.txt": (
        "Rite Way Food Markets - Road Town Tortola\nPusser's Company Store - Road Town\n"
        "CIFC Marina - provisioning on request\nNanny Cay Marina Store - basics only"
    ),
    "agency/crm/leads/enquiries_april.txt": (
        "Lead 1: Sarah M - interested in 7-day BVI trip for honeymoon\n"
        "Lead 2: Tech startup - offsite retreat 10 people\n"
        "Lead 3: Diving club - 8 pax, keen on snorkeling spots"
    ),
    "agency/crm/bookings/confirmed/booking_BK-2024-055.json": json.dumps({
        "booking_id": "BK-2024-055",
        "client": "Rodriguez Family",
        "vessel": "Island Dream",
        "departure": "2024-07-12",
        "duration_days": 7,
        "pax": 6,
        "status": "confirmed",
        "deposit_paid": True
    }, indent=2),
    "agency/crm/bookings/pending/booking_BK-2024-071.json": json.dumps({
        "booking_id": "BK-2024-071",
        "client": "Whitfield Group",
        "vessel": "TBD",
        "departure": "2024-08-03",
        "duration_days": 10,
        "pax": 8,
        "status": "pending_itinerary"
    }, indent=2),
    "legacy/old_system/exports/charter_log_2022.csv": (
        "date,client,days,pax,area,satisfaction\n"
        "2022-03-15,Jones,7,4,BVI,5\n"
        "2022-04-02,Patel,5,6,BVI,4\n"
        "2022-05-18,Chen,10,8,BVI,5"
    ),
    "legacy/old_system/templates/itinerary_template_v1.txt": (
        "ITINERARY TEMPLATE (DEPRECATED - use new system)\n"
        "Day 1: Departure from [BASE_PORT]\n"
        "Day N: Return to base\n"
        "Provisioning: See attached list"
    ),
    "agency/crm/bookings/confirmed/booking_BK-2024-060.txt": (
        "Booking BK-2024-060 | Client: Murphy family | 4 pax | 6 days | vessel: Serenity\n"
        "Status: Confirmed, deposit paid. Awaiting itinerary from planner."
    ),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── THE PROBLEM FILE: messy client charter requests ───────────────────────────
# Contains intentionally messy/wrong values the agent must interpret and map
# to valid plan_charter parameters (days: 3-14, experience: beginner/intermediate/expert,
# interests: snorkeling/dining/remote/nightlife)
messy_requests = [
    {
        "request_id": "REQ-001",
        "client_name": "Harrington Family",
        "trip_length": "7 days",          # valid: days=7
        "num_guests": "4",                 # valid: guests=4
        "sailing_level": "novice",         # INVALID → must map to "beginner"
        "what_they_like": "swimming and eating out",  # maps to "snorkeling,dining"
        "notes": "First time sailing, two young kids"
    },
    {
        "request_id": "REQ-002",
        "client_name": "Whitfield Corporate Group",
        "trip_length": "10 days",          # valid: days=10
        "num_guests": "8",                 # valid: guests=8
        "sailing_level": "advanced",       # INVALID → must map to "expert"
        "what_they_like": "secluded spots and local food",  # maps to "remote,dining"
        "notes": "Executives, have sailed Med before"
    },
    {
        "request_id": "REQ-003",
        "client_name": "Chen Honeymoon",
        "trip_length": "5 days",           # valid: days=5
        "num_guests": "2",                 # valid: guests=2
        "sailing_level": "some experience",  # INVALID → must map to "intermediate"
        "what_they_like": "nightlife and snorkeling",  # maps to "nightlife,snorkeling"
        "notes": "Couple, sailed Caribbean once before"
    },
]

csv_path = os.path.join(workspace, "client_requests.csv")
fieldnames = ["request_id", "client_name", "trip_length", "num_guests",
              "sailing_level", "what_they_like", "notes"]
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(messy_requests)

# ── A brief internal memo (distractor, no hints) ─────────────────────────────
memo_path = os.path.join(workspace, "agency/ops/schedules/planner_memo.txt")
with open(memo_path, "w") as f:
    f.write(
        "TO: Charter Planning Team\n"
        "FROM: Operations Manager\n"
        "DATE: 2024-05-01\n\n"
        "We need proper itinerary documents for the three pending requests in the CRM. "
        "The requests have been captured by sales reps using their own terminology. "
        "Please process them and produce the standard planning output. "
        "Finance needs the provisioning details for each group before end of week.\n"
    )

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 2} total")