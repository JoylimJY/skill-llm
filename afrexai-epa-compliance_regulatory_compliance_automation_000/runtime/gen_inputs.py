import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "facility_ops/maintenance/logs/2023",
    "facility_ops/maintenance/logs/2024",
    "facility_ops/hr/training/safety",
    "facility_ops/hr/training/environmental",
    "permits/air/historical",
    "permits/water/historical",
    "permits/waste/active",
    "records/inspections/2021",
    "records/inspections/2022",
    "records/inspections/2023",
    "reports/financial/Q1",
    "reports/financial/Q2",
    "chemicals/sds/active",
    "chemicals/sds/archived",
    "legal/contracts",
    "legal/violations",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "facility_ops/maintenance/logs/2024/boiler_log.txt": "Boiler inspection passed. Next due: 2025-03-15.",
    "facility_ops/maintenance/logs/2023/hvac_maintenance.csv": "Date,Unit,Status\n2023-01-10,HVAC-1,OK\n2023-06-15,HVAC-2,Repaired",
    "facility_ops/hr/training/safety/ppe_training_roster.txt": "Employee training log - PPE - 42 employees completed 2024-02-01",
    "facility_ops/hr/training/environmental/env_training_roster.txt": "Environmental awareness training - INCOMPLETE - 8 of 47 employees not yet trained - last session: 2022-11-30",
    "permits/air/historical/air_permit_2019.txt": "TX Air Permit #TX-2019-0042 - Expired: 2021-06-30",
    "permits/air/historical/air_permit_2021.txt": "TX Air Permit #TX-2021-0099 - Expired: 2023-06-30",
    "permits/water/historical/npdes_2018.txt": "NPDES Permit TX0012345 - Expired 2020-01-01 - NOT RENEWED",
    "permits/waste/active/epa_id.txt": "EPA Hazardous Waste ID: TXD000111222 - Status: Active",
    "records/inspections/2022/tceq_inspection_2022.txt": "TCEQ Routine Inspection - Date: 2022-08-14\nFindings: NOV issued for improper container labeling, missing accumulation start dates on 3 drums.\nPenalty: $18,500 settled.",
    "records/inspections/2023/internal_audit_2023.txt": "Internal Audit - Dec 2023\nStormwater SWPPP: On-site but NOT updated since 2020.\nSecondary containment: crack observed in east wing electroplating area, liquid seepage noted.\nWeekly waste inspections: last documented inspection 4 months ago.",
    "records/inspections/2021/epa_compliance_eval.txt": "EPA Compliance Evaluation Visit 2021-03-22. No violations found.",
    "reports/financial/Q1/q1_2024_revenue.txt": "Q1 2024 Revenue: $3,200,000. Net Margin: 6.2%",
    "reports/financial/Q2/q2_2024_revenue.txt": "Q2 2024 Revenue: $3,450,000. Net Margin: 5.9%",
    "chemicals/sds/active/chromic_acid_sds.txt": "Chemical: Chromic Acid (Hexavalent Chromium)\nCAS: 7738-94-5\nHazard Class: Oxidizer, Corrosive, Carcinogen\nQuantity on-site: 850 lbs stored in electroplating tank area",
    "chemicals/sds/active/trichloroethylene_sds.txt": "Chemical: Trichloroethylene (TCE)\nCAS: 79-01-6\nHazard Class: VOC, HAP, SVOC\nUsed for: parts degreasing\nAnnual usage: ~2,400 lbs/year",
    "chemicals/sds/active/nickel_sulfate_sds.txt": "Chemical: Nickel Sulfate\nCAS: 7786-81-4\nHazard Class: Toxic, Carcinogen\nQuantity: 320 lbs on-site",
    "chemicals/sds/archived/methylene_chloride_old.txt": "ARCHIVED - Methylene Chloride usage discontinued 2020",
    "legal/violations/nov_2022_settlement.txt": "Notice of Violation 2022-TX-ENV-0892\nViolation: 40 CFR 262.20 - Improper labeling\nSettlement amount: $18,500\nConsent order signed: 2022-11-01",
    "legal/contracts/waste_hauler_contract.txt": "Contract: Clean Disposal LLC - Hazardous Waste Transport\nContract #: CL-2021-441\nExpires: 2025-12-31",
    "facility_ops/hr/training/environmental/rcra_training_log.txt": "RCRA Hazardous Waste Training:\n- Last LQG training conducted: 2022-09-15\n- Personnel trained: 31 of 47\n- Training overdue for: 16 employees",
}

for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# THE CORE INPUT FILE: messy facility profile the agent must process
facility_profile = {
    "facility_name": "Apex Stamping & Plating Co.",
    "location": {
        "state": "Texas",
        "city": "Beaumont",
        "county": "Jefferson County"
    },
    "facility_type": "Automotive parts stamping and electroplating",
    "employees": 47,
    "annual_revenue_usd": 12800000,
    "operations": {
        "processes": [
            "Metal stamping (steel and aluminum blanks)",
            "Electroplating (hexavalent chromium, nickel)",
            "Parts degreasing (trichloroethylene)",
            "On-site wastewater pretreatment"
        ],
        "hazardous_waste_generated_per_month_lbs": 2850,
        "air_emissions": {
            "HAP_tpy": 12.3,
            "VOC_tpy": 85.0,
            "note": "Trichloroethylene is both a HAP and VOC"
        },
        "wastewater_discharge": "Direct discharge to municipal sewer (pretreatment program)"
    },
    "current_permits": {
        "air_permit": {
            "id": "TX-2023-AIR-0442",
            "expiration": "2025-06-30",
            "type": "State air permit - minor source"
        },
        "npdes_permit": "NONE - expired 2020, not renewed",
        "hazardous_waste_epa_id": "TXD000111222",
        "spcc_plan": "NOT ON FILE"
    },
    "last_inspection": {
        "agency": "TCEQ",
        "date": "2022-08-14",
        "result": "NOV issued - settled $18,500"
    },
    "compliance_observations": {
        "permit_currency": "Air permit current; NPDES expired and not renewed; no SPCC plan despite large fuel oil storage (2,400 gal aboveground diesel AST)",
        "waste_management": "EPA ID active but waste inspections lapsed 4 months; containers missing accumulation start dates; secondary containment crack in east wing",
        "reporting_timeliness": "TRI Form R not submitted last year despite TCE usage above threshold; Tier II submitted on time; biennial HW report due this year (even year) - not yet prepared",
        "recordkeeping": "Manifests on file but only 2 years back; some missing LDR notifications",
        "training": "Environmental training: 16 of 47 employees overdue; RCRA training last 2022",
        "spill_prevention": "No SPCC plan; secondary containment breach observed; spill kit inventory not checked in 6 months",
        "air_emissions": "TCE usage 2400 lbs/yr - HAP above 10 tpy threshold; permit listed as minor source which may be incorrect"
    }
}

with open(workspace / "facility_profile.json", "w") as f:
    json.dump(facility_profile, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))}")