#!/usr/bin/env python3
"""
Generate a realistic, messy workspace simulating a property management office
context. Includes distractor files, partial records, unstructured notes, etc.
The agent must use the maintenance CLI to create proper structured entries and
export them — NOT just read these files.
"""

import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Distractor directory structure ───────────────────────────────────────────
dirs = [
    "property_docs/unit_A",
    "property_docs/unit_B",
    "property_docs/unit_C",
    "tenant_records/2023",
    "tenant_records/2024",
    "invoices/plumbing",
    "invoices/electrical",
    "invoices/hvac",
    "inspection_reports/Q1",
    "inspection_reports/Q2",
    "contracts/leases",
    "contracts/vendors",
    "photos_archive",          # distractor — no images, just placeholder
    "old_exports/2022",
    "old_exports/2023",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files (messy, partial, real-world noise) ──────────────────────
distractor_files = {
    "property_docs/unit_A/appliance_notes.txt": (
        "Fridge - bought 2019, still running\n"
        "Oven - needs new burner knob (unit A)\n"
        "Washer/dryer combo - last serviced unknown\n"
    ),
    "property_docs/unit_B/todo_list.txt": (
        "- Fix leaking tap in bathroom\n"
        "- Replace smoke detector battery\n"
        "- Schedule HVAC filter change\n"
        "??? water heater warranty expires soon\n"
    ),
    "property_docs/unit_C/handwritten_scan.txt": (
        "Tenant called about mold near window. Must check.\n"
        "AC not cooling - technician visit pending 2024-05-???\n"
    ),
    "tenant_records/2024/contact_list.csv": (
        "unit,tenant,phone\n"
        "A,John Smith,555-0101\n"
        "B,Maria Garcia,555-0202\n"
        "C,Lee Wong,555-0303\n"
    ),
    "invoices/plumbing/inv_2024_03_leaky_pipe.txt": (
        "Vendor: FastFix Plumbing\n"
        "Date: 2024-03-15\n"
        "Description: Fixed leaking pipe under kitchen sink, Unit B\n"
        "Amount: $185.00\n"
        "Status: PAID\n"
    ),
    "invoices/electrical/inv_2024_04_outlet_repair.txt": (
        "Vendor: Spark Electric Co.\n"
        "Date: 2024-04-02\n"
        "Description: Replaced faulty outlet in living room, Unit A\n"
        "Amount: $95.00\n"
        "Status: UNPAID\n"
    ),
    "invoices/hvac/inv_2024_02_filter_replace.txt": (
        "Vendor: CoolAir Services\n"
        "Date: 2024-02-20\n"
        "Description: Annual HVAC filter replacement, all units\n"
        "Amount: $320.00\n"
        "Status: PAID\n"
    ),
    "inspection_reports/Q1/q1_2024_summary.txt": (
        "Inspection Date: 2024-01-10\n"
        "Inspector: R. Patel\n"
        "Issues Found:\n"
        "  - Unit A: Smoke detector battery low\n"
        "  - Unit B: Bathroom caulking needs replacement\n"
        "  - Unit C: Window seal worn\n"
        "Overall: PASS with minor deficiencies\n"
    ),
    "inspection_reports/Q2/q2_2024_notes.txt": (
        "Pending items from Q1 still open.\n"
        "Need to schedule professional for Unit C mold check.\n"
    ),
    "contracts/vendors/coolair_contract_2024.txt": (
        "Service contract with CoolAir Services\n"
        "Annual value: $320\n"
        "Renewal date: 2025-02-01\n"
    ),
    "contracts/leases/unit_a_lease_2024.txt": (
        "Lease start: 2024-01-01\nLease end: 2024-12-31\nTenant: John Smith\n"
    ),
    "old_exports/2023/maintenance_dump_2023.json": json.dumps({
        "year": 2023,
        "entries": [
            {"type": "repair", "desc": "replaced roof shingles", "cost": 1200},
            {"type": "inventory", "desc": "added new water heater unit B", "cost": 450},
        ]
    }, indent=2),
    "old_exports/2022/legacy_log.txt": (
        "2022-06-01: painted exterior\n"
        "2022-08-15: replaced gate lock\n"
    ),
    "photos_archive/README_PLACEHOLDER.txt": (
        "Photo archive — images stored separately on NAS.\n"
    ),
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ── The actual task specification file ───────────────────────────────────────
# This gives the agent the BUSINESS DATA to record, but deliberately uses
# messy, unstructured language that requires interpretation.
task_brief = """\
PROPERTY MAINTENANCE AUDIT — SPRING 2024
Prepared for: Regional Housing Compliance Office
Reference: RHC-2024-047

Please record the following items in our digital maintenance system and
produce a machine-readable export file called 'audit_export.json' in the
workspace root (/workspace/).

ITEMS TO RECORD:
────────────────

1. ADD ENTRY — General maintenance note:
   "HVAC filter replacement completed for all three units on 2024-02-20"

2. INVENTORY ENTRY:
   "Water heater unit B — installed 2021, 40-gallon, Bradford White brand"

3. SCHEDULE ENTRY:
   "Annual roof inspection scheduled for 2024-09-01 by SkyHigh Roofing Co."

4. COST ENTRY:
   "Plumbing repair Unit B kitchen sink — vendor FastFix Plumbing — $185.00 paid 2024-03-15"

5. LOG ENTRY:
   "Unit C tenant reported mold near north-facing window — investigation pending"

After recording all five items, export ALL data to a JSON file and save it
as 'audit_export.json' in /workspace/.

NOTE: The compliance office requires the JSON export to contain all recorded
entries. Make sure the export is complete before submitting.
"""

(workspace / "AUDIT_BRIEF.txt").write_text(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")