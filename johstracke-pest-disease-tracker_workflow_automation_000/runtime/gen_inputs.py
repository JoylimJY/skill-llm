import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/root/.openclaw/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# Create deeply nested distractor structure simulating a real farm management workspace
dirs = [
    workspace / "farm_logs" / "2023" / "spring",
    workspace / "farm_logs" / "2023" / "summer",
    workspace / "farm_logs" / "2024" / "planning",
    workspace / "soil_tests" / "zone_a",
    workspace / "soil_tests" / "zone_b",
    workspace / "irrigation" / "schedules",
    workspace / "crop_rotation" / "history",
    workspace / "supplier_invoices" / "organic",
    workspace / "compliance" / "audit_2023",
    workspace / "compliance" / "templates",
    workspace / "weather_data",
    workspace / "harvest_records",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but irrelevant
(workspace / "farm_logs" / "2023" / "spring" / "planting_schedule.txt").write_text(
    "Row 1: Tomatoes (Roma, Beefsteak)\nRow 2: Peppers (Bell, Jalapeno)\nRow 3: Cucumbers\n"
)
(workspace / "farm_logs" / "2023" / "summer" / "harvest_log.csv").write_text(
    "date,crop,weight_kg,notes\n2023-07-01,tomatoes,45.2,good yield\n2023-07-15,cucumbers,30.1,some blemishes\n"
)
(workspace / "farm_logs" / "2024" / "planning" / "crop_plan.txt").write_text(
    "2024 Season Plan:\n- Expand tomato section by 20%\n- Introduce companion planting with basil\n- Reduce pesticide use by 30%\n"
)
(workspace / "soil_tests" / "zone_a" / "ph_readings.json").write_text(
    json.dumps({"zone": "A", "readings": [{"date": "2024-01-15", "ph": 6.8}, {"date": "2024-03-01", "ph": 6.5}]}, indent=2)
)
(workspace / "soil_tests" / "zone_b" / "ph_readings.json").write_text(
    json.dumps({"zone": "B", "readings": [{"date": "2024-01-15", "ph": 7.1}, {"date": "2024-03-01", "ph": 6.9}]}, indent=2)
)
(workspace / "irrigation" / "schedules" / "summer_2024.txt").write_text(
    "Monday: Zones A, C - 30 min\nWednesday: Zones B, D - 30 min\nFriday: All zones - 15 min\n"
)
(workspace / "crop_rotation" / "history" / "rotation_2020_2024.csv").write_text(
    "year,zone_a,zone_b,zone_c,zone_d\n2020,tomatoes,peppers,cucumbers,squash\n2021,cucumbers,tomatoes,squash,peppers\n2022,squash,cucumbers,peppers,tomatoes\n"
)
(workspace / "supplier_invoices" / "organic" / "neem_oil_invoice.txt").write_text(
    "Supplier: GreenGarden Co.\nProduct: Neem Oil Concentrate 1L\nQuantity: 5\nUnit Price: $24.99\nTotal: $124.95\n"
)
(workspace / "compliance" / "audit_2023" / "inspection_report.txt").write_text(
    "2023 Audit Result: PASS\nAreas reviewed: pesticide storage, application logs, worker safety\nNext audit: Q2 2024\n"
)
(workspace / "compliance" / "templates" / "incident_template.txt").write_text(
    "INCIDENT REPORT TEMPLATE\nDate:\nLocation:\nProblem:\nSeverity (low/moderate/high/critical):\nAction taken:\nFollow-up required:\n"
)
(workspace / "weather_data" / "june_2024_rainfall.csv").write_text(
    "date,mm_rain,humidity_pct\n2024-06-01,12.3,78\n2024-06-02,0.0,65\n2024-06-03,0.0,60\n2024-06-15,34.5,92\n"
)
(workspace / "harvest_records" / "tomato_yield_2024.json").write_text(
    json.dumps({
        "crop": "tomatoes",
        "variety": "Roma",
        "zone": "A",
        "planted": "2024-04-15",
        "expected_harvest": "2024-07-15",
        "notes": "Monitor for blight given wet June"
    }, indent=2)
)

# A messy, incomplete "notes" file simulating the farmer's raw observations
(workspace / "farm_logs" / "2024" / "planning" / "pest_observations_raw.txt").write_text(
    """RAW FIELD NOTES - June 2024
=================================
June 3: Spotted aphid colonies on new tomato growth in Zone A. Sticky honeydew visible. 
        Estimate 60% of plants affected. URGENT - could spread to peppers.
        
June 5: Squash in Zone C showing powdery white coating on leaves - classic mildew?
        Not too bad yet, maybe 20% of plants. Spreading though.
        
June 8: Early blight confirmed on Zone A tomatoes (lab verified). Dark concentric spots 
        on lower leaves. Rainy weather making it worse. THIS IS CRITICAL - same plants 
        as the aphids!
        
June 10: Cucumber beetles in Zone B - chewing on leaves, concerned about bacterial wilt spread.
         Moderate damage so far.

Planned actions:
- Aphids: neem oil spray, order ladybugs
- Powdery mildew: sulfur fungicide  
- Early blight: copper fungicide + remove bad leaves ASAP
- Cucumber beetles: row covers + beneficial nematodes
""")

print("Workspace initialized with distractor files and raw field notes.")
print(f"Workspace: {workspace}")