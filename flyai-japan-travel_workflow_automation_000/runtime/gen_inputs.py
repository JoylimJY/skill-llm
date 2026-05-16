import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep directory structure with distractor files ──────────────────────────

dirs = [
    "travel_requests/pending",
    "travel_requests/completed",
    "travel_requests/archived",
    "customers/profiles",
    "customers/vip",
    "internal/pricing",
    "internal/supplier_contracts",
    "internal/hr",
    "reports/2024/q1",
    "reports/2024/q2",
    "templates/old",
    "templates/draft",
    "tools/scripts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files

distractors = {
    "travel_requests/pending/bali_request_20240312.txt": "Customer wants 7 days Bali. Beach resort. Budget ¥15000.",
    "travel_requests/pending/korea_request_20240401.txt": "Seoul 4 days, K-pop tour, need hotel near Myeongdong.",
    "travel_requests/completed/thailand_plan_2024.md": "# Thailand 6-Day Plan\n\nDay 1: Bangkok arrival...\nDay 6: Return\n\n✅ Completed",
    "travel_requests/archived/japan_old_2022.txt": "Old Japan trip - outdated pricing. DO NOT USE.",
    "customers/profiles/customer_zhang_wei.json": json.dumps({
        "id": "CUS-0042",
        "name": "张伟",
        "nationality": "Chinese",
        "passport_expiry": "2029-05-12",
        "preferences": ["culture", "food", "photography"],
        "vip": False
    }, ensure_ascii=False, indent=2),
    "customers/profiles/customer_li_hua.json": json.dumps({
        "id": "CUS-0087",
        "name": "李华",
        "nationality": "Chinese",
        "passport_expiry": "2027-11-30",
        "preferences": ["shopping", "onsen", "anime"],
        "vip": True
    }, ensure_ascii=False, indent=2),
    "customers/vip/vip_benefits_2024.txt": "VIP customers get airport lounge access and 10% hotel discount.",
    "internal/pricing/japan_base_rates_2023.csv": "city,hotel_min,hotel_max\nTokyo,300,1200\nKyoto,250,900\nOsaka,200,800\n",
    "internal/pricing/OUTDATED_DO_NOT_USE.txt": "These rates are from 2021 and no longer valid.",
    "internal/supplier_contracts/hotel_partner_jp.txt": "Partner hotels in Japan: APA Group, Dormy Inn, Toyoko Inn.",
    "internal/hr/employee_handbook.pdf.stub": "This is a stub file. Not relevant.",
    "reports/2024/q1/bookings_summary.csv": "month,bookings,revenue\nJan,142,284000\nFeb,98,196000\nMar,201,402000\n",
    "reports/2024/q2/japan_performance.txt": "Japan route bookings up 34% YoY. Cherry blossom season peak.",
    "templates/old/itinerary_v1.md": "# Old Itinerary Template (DEPRECATED)\n\nDo not use this template.",
    "templates/draft/japan_draft_notes.txt": "Notes for Japan template: include JR pass info, visa reminder.",
    "tools/scripts/data_export.py": "# Export tool\nimport csv\n# Not related to current task\n",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── The actual customer request the agent must process ────────────────────────

customer_request = {
    "request_id": "REQ-2024-JP-099",
    "received_at": "2024-10-15T09:32:00+08:00",
    "customer_id": "CUS-0042",
    "customer_name": "张伟",
    "request_type": "full_itinerary",
    "details": {
        "origin_city": "上海",
        "destination_country": "Japan",
        "departure_date": "2024-11-20",
        "return_date": "2024-11-24",
        "trip_days": 5,
        "cities_requested": None,
        "notes": "First time visiting Japan. No specific preference — wants the classic experience. Budget is medium range.",
        "special_requirements": "Please include visa information as customer is unsure if visa is needed."
    },
    "assigned_agent": "auto",
    "status": "pending_plan"
}

with open(os.path.join(workspace, "travel_requests/pending/japan_request_REQ-2024-JP-099.json"), "w", encoding="utf-8") as f:
    json.dump(customer_request, f, ensure_ascii=False, indent=2)

# ── A partial/wrong previous attempt (distractor) ────────────────────────────

bad_attempt = """# Japan Trip Draft (INCOMPLETE - DO NOT SEND TO CUSTOMER)

Day 1: Tokyo
- Do some sightseeing
- Check in to hotel

Day 2: Free day in Tokyo

Day 3: Kyoto maybe?

Day 4: Free activities

Day 5: Return

TODO: Add flight info, hotels, visa info
"""
with open(os.path.join(workspace, "travel_requests/pending/japan_REQ-099_DRAFT_INCOMPLETE.md"), "w", encoding="utf-8") as f:
    f.write(bad_attempt)

print("Workspace generated successfully.")
print(f"Key file: {workspace}/travel_requests/pending/japan_request_REQ-2024-JP-099.json")