import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Deep directory structure with distractor files ──────────────────────────
dirs = [
    "plant_ops/maintenance/schedules",
    "plant_ops/maintenance/logs",
    "plant_ops/production/shift_reports",
    "plant_ops/production/quality",
    "hr/onboarding/documents",
    "hr/payroll/2024",
    "hr/training/certificates",
    "facilities/floor_plans",
    "facilities/equipment_inventory",
    "compliance/environmental",
    "compliance/safety_old",
    "compliance/legal",
    "it/network",
    "it/software_licenses",
    "finance/invoices/q1_2024",
    "finance/invoices/q2_2024",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "plant_ops/maintenance/schedules/forklift_pm_schedule.csv": (
        "Asset,Last PM Date,Next Due,Technician\n"
        "Forklift-01,2024-03-15,2024-06-15,J.Torres\n"
        "Forklift-02,2024-02-20,2024-05-20,J.Torres\n"
        "Press-01,2024-01-10,2024-04-10,M.Singh\n"
    ),
    "plant_ops/maintenance/logs/repair_log_may2024.txt": (
        "2024-05-02 - Forklift-02 hydraulic fluid leak - repaired by J.Torres\n"
        "2024-05-10 - Welding station exhaust fan replaced - M.Singh\n"
        "2024-05-18 - Emergency eyewash station #3 - monthly flush performed\n"
    ),
    "plant_ops/production/shift_reports/shift_A_june2024.txt": (
        "Shift A Report - June 3, 2024\n"
        "Supervisor: Linda Marsh\n"
        "Units produced: 847\n"
        "Downtime: 45 min (press jam)\n"
        "Notes: Near-miss forklift incident in aisle 7 at 10:22 AM - reported to safety coordinator\n"
    ),
    "plant_ops/production/quality/defect_log_q2.csv": (
        "Date,Part,Defect Type,Qty,Disposition\n"
        "2024-04-05,Bracket-A,Dimension,12,Scrap\n"
        "2024-05-22,Shaft-B,Surface finish,4,Rework\n"
    ),
    "hr/onboarding/documents/new_hire_checklist.txt": (
        "New Hire Checklist:\n"
        "[ ] ID badge\n"
        "[ ] Uniform issue\n"
        "[ ] Benefits enrollment\n"
        "[ ] IT access\n"
        "[ ] Safety video (30 min)\n"
    ),
    "hr/training/certificates/forklift_operator_certs.txt": (
        "Certified operators (expires 3 years from issue):\n"
        "R. Mendez - issued 2022-01-15 - expires 2025-01-15\n"
        "T. Brown - issued 2021-06-01 - EXPIRED\n"
        "K. Patel - issued 2023-03-10 - expires 2026-03-10\n"
    ),
    "hr/payroll/2024/payroll_summary_q1.txt": (
        "Q1 2024 Payroll Summary\n"
        "Total employees: 78\n"
        "Total wages: $1,243,000\n"
        "Overtime: $87,000\n"
    ),
    "facilities/equipment_inventory/machine_register.csv": (
        "ID,Type,Location,Install Year,Last Inspection\n"
        "P-01,Hydraulic Press,Bay 1,2017,2023-11-01\n"
        "W-01,MIG Welder,Bay 2,2019,2024-01-15\n"
        "W-02,TIG Welder,Bay 2,2020,2024-01-15\n"
        "FK-01,Forklift Toyota,Warehouse,2021,2024-02-10\n"
        "FK-02,Forklift Crown,Warehouse,2018,2023-09-05\n"
        "CNC-01,CNC Lathe,Bay 3,2022,2024-03-01\n"
    ),
    "facilities/floor_plans/bay_layout_notes.txt": (
        "Bay 1: Hydraulic presses, stamping - high noise zone (>90dB)\n"
        "Bay 2: Welding stations - fume extraction installed 2022\n"
        "Bay 3: CNC machining - coolant floor hazard\n"
        "Warehouse: Forklift traffic, racking 24ft high\n"
        "Mezzanine: Parts storage, access via fixed ladder - no guardrails on east side\n"
    ),
    "compliance/environmental/epa_tier_ii_2023.txt": (
        "EPA Tier II Chemicals on site:\n"
        "- Acetylene (welding): 500 lbs\n"
        "- Hydraulic oil: 2000 gal\n"
        "- Cutting fluid (mineral oil): 800 gal\n"
        "- Zinc chromate primer: 200 lbs\n"
    ),
    "compliance/safety_old/safety_manual_2019.txt": (
        "Riverside Metal Works Safety Manual - Rev 2019\n"
        "Last updated: March 2019\n"
        "LOTO procedure: See appendix A (not attached)\n"
        "PPE policy: Hard hats and safety glasses required in bays\n"
        "Emergency plan: Call 911, evacuate to parking lot\n"
        "Note: This document is outdated. A current version has not been issued.\n"
    ),
    "compliance/legal/osha_inspection_letter_2024.txt": (
        "OSHA Area Office - Midwest Region\n"
        "Date: May 28, 2024\n"
        "To: Riverside Metal Works, Attn: Plant Manager\n"
        "Re: Follow-up Inspection Scheduled\n\n"
        "Following our programmed inspection on May 15, 2024, a follow-up inspection "
        "is scheduled for 90 days hence. During the initial visit, inspectors noted "
        "potential concerns in the following areas:\n"
        "1. Lockout/Tagout procedures - no written program observed\n"
        "2. Fall protection on mezzanine east side\n"
        "3. Forklift operator training records - one operator with expired certification\n"
        "4. Hazard Communication - SDS binder not accessible at welding stations\n"
        "5. No formal incident investigation program documented\n\n"
        "Failure to abate may result in additional citations.\n"
        "Sincerely,\nArea Director, OSHA Midwest\n"
    ),
    "compliance/legal/penalty_notice_draft.txt": (
        "DRAFT - Not yet filed\n"
        "Potential citation items under review:\n"
        "- Serious: LOTO\n"
        "- Serious: Fall protection\n"
        "- Other-than-serious: Training records\n"
    ),
    "it/software_licenses/erp_licenses.txt": (
        "ERP: SAP S/4HANA - 80 user licenses - expires 2025-12-31\n"
        "MES: Plex Systems - 40 licenses - expires 2025-06-30\n"
    ),
    "finance/invoices/q2_2024/vendor_summary.csv": (
        "Vendor,Invoice#,Amount,Date,Status\n"
        "ABC Welding Supply,INV-4421,$3,200,2024-04-10,Paid\n"
        "Safety First Inc,INV-0892,$1,450,2024-05-01,Pending\n"
        "Forklift Service Co,INV-3310,$2,800,2024-04-28,Paid\n"
    ),
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")

# ── The actual task brief (not a hint file — just raw context data) ──────────
# This is the messy input the agent receives: a raw notes dump from the plant manager
brief_path = workspace / "compliance" / "safety_task_brief.txt"
brief_path.write_text(
    "RIVERSIDE METAL WORKS — SAFETY DOCUMENTATION REQUEST\n"
    "Plant: Riverside Metal Works, Dayton OH\n"
    "Industry: Metal fabrication / manufacturing\n"
    "Employees: 78 total (60 production, 12 warehouse, 6 office)\n"
    "\n"
    "RECENT INCIDENTS (last 12 months):\n"
    "- June 3, 2024: Near-miss — Forklift FK-02 almost struck pedestrian worker R. Mendez\n"
    "  in warehouse aisle 7 at 10:22 AM. No injury. Operator: T. Brown (expired cert).\n"
    "- Feb 14, 2024: First aid — Worker cut hand on unguarded press die at Bay 1.\n"
    "  Treated on-site. Lost no time.\n"
    "- Nov 8, 2023: Recordable — Welder inhaled fumes (fume extractor offline 3 days).\n"
    "  3 restricted work days.\n"
    "\n"
    "CURRENT SAFETY PROGRAMS IN PLACE:\n"
    "- Outdated 2019 safety manual (no LOTO, no confined space, no written fall protection)\n"
    "- No formal HazCom/SDS program at workstations\n"
    "- Basic first aid kit and eyewash stations present\n"
    "- No incident investigation process documented\n"
    "- Forklift operator training — some expired certs\n"
    "\n"
    "OSHA FOLLOW-UP INSPECTION IN ~90 DAYS.\n"
    "We need complete safety documentation ASAP.\n",
    encoding="utf-8",
)

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))} items")