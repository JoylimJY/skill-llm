import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── distractor directory tree ──────────────────────────────────────────────
dirs = [
    "field_ops/equipment",
    "field_ops/vehicles",
    "field_ops/shelter",
    "field_ops/personnel",
    "logistics/inventory",
    "logistics/checklists",
    "training/modules",
    "training/assessments",
    "reports/weekly",
    "reports/incidents",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files (not relevant to the task)
distractors = {
    "field_ops/equipment/carabiner_specs.txt": (
        "Carabiner model: HMS-3\nGate type: Screwgate\nRated load: 25 kN\n"
        "Suitable for: belaying, anchor attachment\nNOTE: not a rope substitute\n"
    ),
    "field_ops/equipment/tent_peg_inventory.csv": (
        "peg_id,material,length_cm,qty\n"
        "T01,titanium,18,24\nT02,steel,22,48\nT03,plastic,15,60\n"
    ),
    "field_ops/vehicles/truck_manifest_2024.json": json.dumps({
        "truck_id": "TRK-07",
        "payload_kg": 1200,
        "tie_down_points": 8,
        "notes": "rear gate reinforced 2023"
    }, indent=2),
    "field_ops/vehicles/roof_rack_dimensions.txt": (
        "Rack model: ExploreMax 220\nMax load: 150 kg\nBar width: 1.4 m\n"
        "Bar spacing: 0.9 m\nCompatible rope diameter: 8-12 mm\n"
    ),
    "field_ops/shelter/tarp_models.csv": (
        "model,size_m,weight_kg,grommet_spacing_cm\n"
        "HeavyDuty-8x6,8x6,2.1,60\nUltraLight-4x3,4x3,0.6,50\n"
    ),
    "field_ops/shelter/shelter_failures_2023.txt": (
        "Incident 1: tarp collapsed during storm — guy lines failed\n"
        "Incident 2: pole lashing slipped — structure fell\n"
        "Incident 3: load shifted on roof rack — securing line came loose\n"
        "Root cause analysis pending.\n"
    ),
    "field_ops/personnel/crew_roster.txt": (
        "Alpha Team: 6 members\nBeta Team: 4 members\nTraining level: mixed\n"
        "Last rope skills assessment: 18 months ago\n"
    ),
    "logistics/inventory/rope_stock.csv": (
        "rope_id,material,diameter_mm,length_m,breaking_strength_kg,qty\n"
        "R01,nylon,10,30,2000,5\n"
        "R02,polyester,8,50,1400,8\n"
        "R03,polypropylene,6,100,600,12\n"
        "R04,manila,12,20,1800,3\n"
        "R05,dyneema,4,30,2500,2\n"
    ),
    "logistics/checklists/pre_departure.txt": (
        "[ ] Fuel check\n[ ] First aid kit\n[ ] Navigation tools\n"
        "[ ] Rope and lashing gear\n[ ] Communication devices\n"
    ),
    "training/modules/old_knot_guide_DRAFT.txt": (
        "DRAFT - DO NOT USE - SUPERSEDED\n"
        "Square knot: tie right over left, left over right. Good for all joining tasks.\n"
        "NOTE: This draft is INCORRECT and has been recalled.\n"
    ),
    "training/assessments/crew_results_2023.json": json.dumps({
        "assessment_date": "2023-09-15",
        "crew_pass_rate": 0.52,
        "common_failures": [
            "Used square knot for load joining",
            "Taut-line only had one inner wrap",
            "Lashing frapping turns missing"
        ]
    }, indent=2),
    "reports/weekly/week_42_summary.txt": (
        "Equipment losses: 1 tarp\nRope condition: 3 lines flagged for retirement\n"
        "Training gap identified: securing loads, lashing technique\n"
    ),
    "reports/incidents/INC-2023-11.txt": (
        "Date: 2023-11-03\nDescription: Load shifted causing minor damage.\n"
        "Contributing factor: incorrect knot used for tensioning.\n"
        "Recommendation: mandatory rope skills refresher.\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── THE ACTUAL PROBLEM INPUT ───────────────────────────────────────────────
# A scenario specification file the agent must process.
# It contains 5 field scenarios with messy/ambiguous descriptions.
# The agent must produce a structured decision guide JSON.

scenarios = {
    "expedition_scenarios": [
        {
            "scenario_id": "S1",
            "description": (
                "We need to secure 480 kg of camping gear on the roof rack of TRK-07. "
                "The rope we have is 10mm nylon with a 2000 kg breaking strength. "
                "We want it pulled as tight as possible — hand tension alone never works. "
                "The attachment points are two fixed rings on the rack front and rear."
            ),
            "requirements": ["maximum_tension", "truck_load_securing"],
            "adjustability_needed": False,
            "quick_release_needed": False
        },
        {
            "scenario_id": "S2",
            "description": (
                "Setting up tarp guy lines at camp. Lines need to be adjustable after "
                "staking — we want to be able to tighten or loosen them from outside "
                "the tarp without untying. Stakes are metal T-pegs. "
                "Rope is 6mm polypropylene."
            ),
            "requirements": ["adjustable_tension", "tarp_setup"],
            "adjustability_needed": True,
            "quick_release_needed": False
        },
        {
            "scenario_id": "S3",
            "description": (
                "We have a 12mm manila rope and a 6mm polyester cord we need to join "
                "together to reach a distant anchor point. Total load on the joined "
                "line will be about 150 kg. It does not need to be permanent."
            ),
            "requirements": ["rope_joining", "different_diameters"],
            "adjustability_needed": False,
            "quick_release_needed": False
        },
        {
            "scenario_id": "S4",
            "description": (
                "Building a camp table frame using four vertical poles and two "
                "horizontal cross-members at right angles. Need to lash the joints "
                "where horizontal meets vertical. Also need diagonal bracing poles "
                "crossing at approximately 45 degrees to stop the frame racking."
            ),
            "requirements": ["right_angle_joints", "diagonal_bracing", "pole_structure"],
            "adjustability_needed": False,
            "quick_release_needed": False
        },
        {
            "scenario_id": "S5",
            "description": (
                "Crew member asked if the square knot is okay for joining the two "
                "sections of our main haul line (8mm polyester, estimated 300 kg peak "
                "load). We need an official answer to include in the safety guide."
            ),
            "requirements": ["knot_safety_ruling", "load_bearing_join"],
            "adjustability_needed": False,
            "quick_release_needed": False
        }
    ],
    "metadata": {
        "prepared_by": "field_coordinator",
        "date": "2024-03-15",
        "purpose": "Input for crew rope-skills decision guide",
        "status": "awaiting_expert_review"
    }
}

input_path = os.path.join(workspace, "field_ops", "equipment", "expedition_scenarios.json")
with open(input_path, "w") as f:
    json.dump(scenarios, f, indent=2)

print("Workspace generated successfully.")
print(f"Scenario input: {input_path}")
print(f"Total distractor files: {len(distractors)}")