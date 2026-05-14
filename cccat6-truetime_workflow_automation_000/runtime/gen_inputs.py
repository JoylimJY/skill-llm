import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE", "/workspace"))

# ─── Directory structure ───────────────────────────────────────────────────────
dirs = [
    "pharma_logistics/shipments/EU_hub",
    "pharma_logistics/shipments/APAC_hub",
    "pharma_logistics/shipments/US_hub",
    "pharma_logistics/compliance/cold_chain",
    "pharma_logistics/compliance/regulatory",
    "pharma_logistics/schedules/pending",
    "pharma_logistics/schedules/confirmed",
    "pharma_logistics/contacts",
    "pharma_logistics/assets/labels",
    "pharma_logistics/assets/manifests",
    "pharma_logistics/archive/2023",
    "pharma_logistics/archive/2024",
    "internal/ops_tools",
    "internal/monitoring",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "pharma_logistics/shipments/EU_hub/shipment_EU-2041.json": {
        "shipment_id": "EU-2041",
        "drug": "Cryovax-B",
        "temp_range_c": [-20, -15],
        "origin": "Frankfurt",
        "destination": "Warsaw",
        "status": "in_transit",
    },
    "pharma_logistics/shipments/APAC_hub/shipment_APAC-0987.json": {
        "shipment_id": "APAC-0987",
        "drug": "HepaCure-IV",
        "temp_range_c": [2, 8],
        "origin": "Shanghai",
        "destination": "Tokyo",
        "status": "pending_clearance",
    },
    "pharma_logistics/shipments/US_hub/shipment_US-3312.json": {
        "shipment_id": "US-3312",
        "drug": "NeuroPatch-7",
        "temp_range_c": [15, 25],
        "origin": "Chicago",
        "destination": "Los Angeles",
        "status": "awaiting_dispatch",
    },
    "pharma_logistics/compliance/cold_chain/temp_log_2024Q4.csv": "timestamp,sensor_id,temp_c\n2024-10-01T00:00:00Z,SN-001,4.2\n2024-10-01T01:00:00Z,SN-001,4.5\n",
    "pharma_logistics/compliance/regulatory/import_permit_EU.txt": "Permit No: EU/2024/98432\nValid Until: 2025-06-30\nDrug Class: Biologic\n",
    "pharma_logistics/contacts/hub_managers.json": {
        "EU": {"name": "Greta Hoffmann", "tz": "Europe/Berlin", "email": "g.hoffmann@pharmahub.eu"},
        "APAC": {"name": "Liang Wei", "tz": "Asia/Shanghai", "email": "l.wei@pharmahub.cn"},
        "US": {"name": "Sandra Kowalski", "tz": "America/Chicago", "email": "s.kowalski@pharmahub.us"},
    },
    "pharma_logistics/assets/manifests/manifest_template.json": {
        "version": "2.1",
        "fields": ["shipment_id", "drug_name", "quantity_units", "batch_no", "dispatch_utc", "arrival_utc"],
    },
    "pharma_logistics/assets/labels/barcode_spec.txt": "Format: GS1-128\nMax length: 48 chars\nEncoding: UTF-8\n",
    "pharma_logistics/archive/2023/summary_2023.txt": "Total shipments: 1204\nOn-time delivery rate: 97.3%\nCold chain breaches: 3\n",
    "pharma_logistics/archive/2024/summary_2024.txt": "Total shipments: 1389\nOn-time delivery rate: 98.1%\nCold chain breaches: 1\n",
    "internal/ops_tools/timezone_cheatsheet.txt": (
        "WRONG OFFSETS - DO NOT USE\n"
        "CST = could be UTC-6, UTC+8, or UTC-5:30 -- AMBIGUOUS\n"
        "IST = UTC+5:30 or UTC+2 or UTC+1 -- AMBIGUOUS\n"
        "Always use IANA names!\n"
    ),
    "internal/monitoring/ntp_hosts.txt": "time.google.com\npool.ntp.org\ntime.cloudflare.com\n",
    "pharma_logistics/schedules/pending/placeholder.txt": "No confirmed schedules yet.\n",
    "pharma_logistics/schedules/confirmed/placeholder.txt": "Empty.\n",
}

for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, dict) or isinstance(content, list):
        fpath.write_text(json.dumps(content, indent=2))
    else:
        fpath.write_text(content)

# ─── THE CORE TASK INPUT ───────────────────────────────────────────────────────
# This is the "messy briefing" the agent must interpret to produce schedule_report.json

briefing = {
    "task": "Generate schedule_report.json with three checkpoint entries for the Q3 cold-chain audit.",
    "checkpoints": [
        {
            "id": "CP-1",
            "description": "Calendar-based quality review deadline",
            "scheduling_note": (
                "The EU hub manager in Frankfurt needs a quality review 2.5 months from now. "
                "Calendar arithmetic should be anchored to Europe/Berlin. "
                "Show the result in Europe/Berlin local time."
            ),
            "required_output_fields": [
                "now_utc", "target_utc", "target_user_tz",
                "delta_milliseconds", "time_source",
                "now_lunar", "target_lunar"
            ],
        },
        {
            "id": "CP-2",
            "description": "Cross-timezone sync meeting — absolute target",
            "scheduling_note": (
                "A regulatory sync meeting is fixed at 2026-09-15 at 10:00 AM in Tokyo (Asia/Tokyo). "
                "Report what time this is for the US Chicago hub manager (America/Chicago). "
                "Note: September is outside DST ambiguity in Tokyo, but Chicago will be in CDT."
            ),
            "required_output_fields": [
                "now_utc", "target_utc", "target_user_tz",
                "delta_milliseconds", "time_source",
                "now_lunar", "target_lunar"
            ],
        },
        {
            "id": "CP-3",
            "description": "NTP-verified dispatch window",
            "scheduling_note": (
                "The US hub needs a dispatch window starting exactly 45 minutes from now, "
                "verified against network time (do NOT use server clock). "
                "User timezone is America/Chicago."
            ),
            "required_output_fields": [
                "now_utc", "target_utc", "target_user_tz",
                "delta_milliseconds", "time_source", "ntp_server",
                "now_lunar", "target_lunar"
            ],
        },
    ],
    "output_file": "schedule_report.json",
    "output_format": (
        "A JSON object with a top-level key 'checkpoints' containing a list of objects, "
        "one per checkpoint, each with at minimum the fields listed in required_output_fields "
        "plus 'id' and 'description'."
    ),
}

briefing_path = workspace / "pharma_logistics" / "schedules" / "pending" / "q3_audit_briefing.json"
briefing_path.write_text(json.dumps(briefing, indent=2))

print(f"Workspace initialized at {workspace}")
print(f"Briefing written to {briefing_path}")