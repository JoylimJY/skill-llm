import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))

# --- Directory structure with distractor files ---
dirs = [
    "scripts",
    "projects/pellet_plant_alpha",
    "projects/pellet_plant_alpha/docs",
    "projects/pellet_plant_alpha/data",
    "projects/biomass_audit",
    "projects/biomass_audit/raw",
    "archive/old_reports",
    "archive/templates",
    "config",
    "logs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Realistic mock script.sh that returns domain-specific content ---
# This is the actual skill script the agent needs to invoke.
script_sh = r"""#!/usr/bin/env bash
COMMAND="${1:-help}"

case "$COMMAND" in
  intro)
    cat <<'EOF'
=== BIOMASS ENERGY — INTRODUCTION ===
Biomass is organic material from plants, animals, and waste used for energy.
Global biomass energy contributes approximately 10% of total primary energy supply.
Major conversion pathways: Combustion, Gasification, Pyrolysis, Fermentation.
Key advantages: Carbon-neutral (net), dispatchable, widely available feedstocks.
Regional leaders: EU, USA, Brazil, China.
EOF
    ;;
  feedstocks)
    cat <<'EOF'
=== BIOMASS FEEDSTOCKS ===
Feedstock             | HHV (MJ/kg dry) | Moisture % (typical) | Ash % (dry basis) | Bulk Density (kg/m³)
----------------------|-----------------|----------------------|-------------------|---------------------
Wood chips            | 18.5–19.5       | 30–55                | 0.5–2.0           | 200–350
Sawdust               | 18.0–19.0       | 20–55                | 0.3–1.5           | 150–250
Agricultural straw    | 16.5–18.0       | 10–25                | 4.0–12.0          | 80–150
Energy crops (Miscanthus)| 17.5–18.5   | 15–25                | 1.5–4.0           | 100–200
Wood pellets          | 17.0–18.5       | 6–10                 | 0.3–1.5           | 550–750
Bark                  | 18.0–21.0       | 30–60                | 2.0–6.0           | 250–450
Rice husk             | 13.0–15.0       | 8–14                 | 15.0–25.0         | 80–130
Olive residue         | 20.0–22.0       | 20–45                | 2.5–8.0           | 300–500

Notes:
- HHV = Higher Heating Value (dry, ash-free basis approximated above)
- Moisture content dramatically reduces Net Calorific Value (NCV)
- Ash content affects slagging, fouling, and emissions
- Feedstocks with ash >6% (dry) are generally unsuitable for premium pellets
EOF
    ;;
  combustion)
    cat <<'EOF'
=== BIOMASS COMBUSTION ===
Technologies:
  - Grate combustion: most common for solid biomass, capacities 1–100 MW
  - Fluidized bed (BFB/CFB): high efficiency, tolerates variable fuel, >10 MW
  - Stoker: fixed/moving grate, residential to medium industrial
Efficiency:
  - Small grate: 65–78%
  - Large fluidized bed: 80–92%
Combustion air:
  - Primary air: under-grate or primary zone, 60–80% of stoichiometric
  - Secondary air: overfire, 20–40% of stoichiometric
  - Excess air typical: 20–40%
Key parameter: Lambda (λ) = actual air / stoichiometric air; optimal λ = 1.2–1.4
Stoichiometric air requirement: ~4.6–5.5 Nm³/kg dry biomass (varies by feedstock)
EOF
    ;;
  gasification)
    cat <<'EOF'
=== BIOMASS GASIFICATION ===
Technologies:
  - Updraft (counter-current): simple, high tar, 1–10 MW
  - Downdraft (co-current): low tar, suitable for engines, 10 kW–1 MW
  - Fluidized bed: high throughput, variable fuel, 5–100 MW
Syngas composition (typical, downdraft, wood):
  - CO: 17–22%
  - H2: 15–21%
  - CO2: 9–15%
  - CH4: 1–5%
  - N2: 45–55%
  - Tars: <1 g/Nm³ (downdraft) vs 10–150 g/Nm³ (updraft)
Cold Gas Efficiency (CGE): 60–80%
Gasification temperature: 700–1000°C
Equivalence Ratio (ER): 0.2–0.4
Heating value of syngas: 4–6 MJ/Nm³ (LHV, air-blown, N2 diluted)
EOF
    ;;
  pyrolysis)
    cat <<'EOF'
=== BIOMASS PYROLYSIS ===
Modes and product distribution:
  Mode         | Temp (°C) | Heating Rate | Residence Time | Biochar % | Bio-oil % | Syngas %
  -------------|-----------|--------------|----------------|-----------|-----------|----------
  Slow          | 300–500   | Low (<10°C/s)| Hours–days     | 25–35     | 25–35     | 30–40
  Fast          | 450–600   | High (>100°C/s)| Seconds      | 10–20     | 55–75     | 10–20
  Flash         | 700–1000  | Very high    | <1 second      | 5–10      | 60–75     | 15–25

Bio-oil properties:
  - Water content: 15–30%
  - HHV: 14–19 MJ/kg
  - pH: 2–3 (acidic)
  - Viscosity: 25–1000 cP (highly variable)
  - Not directly fungible with petroleum — requires upgrading for fuel use

Biochar:
  - Fixed carbon: 50–90%
  - HHV: 25–32 MJ/kg
  - Applications: soil amendment, activated carbon precursor, co-firing

Feedstock requirement: moisture <10% recommended for fast pyrolysis
EOF
    ;;
  pellets)
    cat <<'EOF'
=== BIOMASS PELLETIZATION ===
Process steps:
  1. Feedstock reception and sorting
  2. Size reduction (chipping/grinding) — target particle size: <4 mm (80% passing)
  3. Drying — target moisture: 8–12% for pressing
  4. Conditioning (steam/water addition) — raises temperature to 70–90°C
  5. Pellet press (ring-die or flat-die)
  6. Cooling (counter-flow cooler) — reduces pellet temperature to <10°C above ambient
  7. Screening — removes fines
  8. Storage and packaging

ENplus Quality Classes (wood pellets):
  Class    | Diameter (mm) | Length     | Moisture | Ash %   | HHV (MJ/kg) | Fines (<3.15mm) | Mech. Durability
  ---------|---------------|------------|----------|---------|-------------|-----------------|------------------
  ENplus-A1| 6 or 8        | 3.15–40mm  | ≤10%     | ≤0.7%   | ≥16.5       | ≤1.0%           | ≥98.0%
  ENplus-A2| 6 or 8        | 3.15–40mm  | ≤10%     | ≤1.2%   | ≥16.5       | ≤1.0%           | ≥97.5%
  ENplus-B | 6 or 8        | 3.15–40mm  | ≤10%     | ≤2.0%   | ≥16.5       | ≤1.0%           | ≥97.5%

Press types:
  - Ring-die press: high throughput (1–10 t/h per unit), industrial scale
  - Flat-die press: lower throughput (<1 t/h), small/farm scale

Energy consumption for pelletizing: 60–150 kWh/tonne pellets produced
Binder: Not required for wood; sometimes used for agricultural residues (starch, molasses)
Pellet density: ≥600 kg/m³ (bulk: 550–750 kg/m³)
EOF
    ;;
  emissions)
    cat <<'EOF'
=== BIOMASS EMISSIONS ===
Particulate Matter (PM):
  - Grate combustion: 200–2000 mg/Nm³ (uncontrolled)
  - With electrostatic precipitator (ESP): <20 mg/Nm³
  - EU Ecodesign 2022 limit (pellet stoves): <40 mg/Nm³
NOx:
  - Biomass NOx: 100–400 mg/Nm³ (primarily fuel-NOx from proteins)
  - Flue gas recirculation (FGR) reduces NOx by 30–50%
CO:
  - Poor combustion: 500–5000 mg/Nm³
  - Well-tuned system: <100 mg/Nm³
SO2:
  - Wood biomass: very low SO2 (<100 mg/Nm³) due to low sulfur content
  - Agricultural residues: higher SO2 (100–500 mg/Nm³)
Carbon:
  - Lifecycle CO2: 15–30 g CO2eq/kWh (vs coal: 900–1050 g CO2eq/kWh)
EOF
    ;;
  sizing)
    cat <<'EOF'
=== BIOMASS PLANT SIZING ===
Rules of thumb:

1. Fuel Consumption:
   fuel_consumption_tph = thermal_output_MW / (NCV_MJ_per_kg * boiler_efficiency)
   (where NCV in MJ/kg, efficiency as decimal, result in tonnes/hour)

2. Net Calorific Value (NCV) from moisture:
   NCV_MJ_per_kg = HHV_dry * (1 - MC) - 2.45 * MC
   (where MC = moisture content as decimal, HHV_dry in MJ/kg, 2.45 is latent heat factor MJ/kg water)

3. Annual Fuel Requirement:
   annual_tonnes = fuel_consumption_tph * operating_hours_per_year

4. Storage volume:
   storage_days_recommended = 7–30 days (depending on supply chain risk)
   storage_m3 = (annual_tonnes / 365) * storage_days * (1 / bulk_density_t_per_m3)

5. Boiler Capacity Rule:
   - For redundancy: install 2 boilers each at 60–70% of peak load
   - Minimum turndown ratio: 30% of rated capacity

6. Pellet Plant Throughput:
   - Dryer capacity must match press throughput
   - Press utilization target: 75–85% of rated capacity
   - Quality control: sample every 2 hours per ENplus audit protocol

7. Electrical demand:
   - Pellet plant auxiliary load: approximately 35–50 kWh per tonne of pellets
   - Includes: grinding, drying fan, press, cooler, conveyors

Note: 1 tonne = 1000 kg. Bulk density for wood chips ~250 kg/m³, wood pellets ~650 kg/m³.
EOF
    ;;
  help)
    cat <<'EOF'
Biomass Energy Reference — Available Commands:
  intro        Overview of biomass energy
  feedstocks   Feedstock properties (HHV, moisture, ash, density)
  combustion   Combustion technologies and efficiency
  gasification Gasification technologies and syngas data
  pyrolysis    Pyrolysis modes and product distributions
  pellets      Pelletization process and ENplus quality standards
  emissions    Emission profiles and limits
  sizing       Plant sizing calculations and rules of thumb
  help         Show this help
  version      Show version info
EOF
    ;;
  version)
    echo "biomass skill v1.0.0 — BytesAgain"
    ;;
  *)
    echo "Unknown command: $COMMAND"
    echo "Run: scripts/script.sh help"
    exit 1
    ;;
esac
"""

with open(WORKSPACE / "scripts" / "script.sh", "w") as f:
    f.write(script_sh)

# --- Project context file (the business scenario) ---
project_brief = """PELLET PLANT ALPHA — PROJECT BRIEF
Client: NordicGreen Energy AS
Site: Trondheim, Norway
Capacity target: 8 MW thermal output (planned district heating)
Feedstock: Sawdust (locally sourced, moisture 45%)
Operating hours: 7800 hours/year
Boiler type: Grate combustion
Boiler efficiency: 82%
Storage target: 14 days
Target pellet quality: ENplus-A1 certification

NOTE: This brief requires a feasibility_report.json to be produced
using the internal biomass reference tooling available in this workspace.
The report must include verified technical parameters from the reference system.
"""
with open(WORKSPACE / "projects" / "pellet_plant_alpha" / "docs" / "project_brief.txt", "w") as f:
    f.write(project_brief)

# --- Distractor files ---
distractors = {
    "projects/pellet_plant_alpha/data/cost_estimate_v2.csv": (
        "item,unit_cost_EUR,quantity\n"
        "ring_die_press,180000,2\n"
        "counter_flow_cooler,45000,1\n"
        "drum_dryer,120000,1\n"
        "hammer_mill,35000,2\n"
        "storage_silo,60000,3\n"
    ),
    "projects/pellet_plant_alpha/data/supplier_quotes.txt": (
        "Supplier A: Andritz — Ring die press 5t/h — EUR 175,000\n"
        "Supplier B: CPM — Ring die press 3t/h — EUR 130,000\n"
        "Supplier C: Amandus Kahl — Flat die press 0.8t/h — EUR 28,000\n"
    ),
    "projects/biomass_audit/raw/site_survey_2023.txt": (
        "Site inspection: Trondheim depot\n"
        "Available area: 12,000 m2\n"
        "Road access: HGV suitable\n"
        "Rail siding: No\n"
        "Grid connection: 11kV, 2MW available\n"
        "Water: Municipal supply\n"
    ),
    "projects/biomass_audit/raw/feedstock_samples.csv": (
        "sample_id,feedstock,mc_percent,ash_percent,origin\n"
        "S001,Sawdust,44,0.9,Moelven Mill\n"
        "S002,Sawdust,46,0.8,Norske Skog\n"
        "S003,Wood chips,52,1.1,Local forest\n"
        "S004,Bark,55,3.2,Borregaard\n"
        "S005,Sawdust,43,1.0,Svartedalens\n"
    ),
    "archive/old_reports/pellet_feasibility_2019.txt": (
        "OBSOLETE REPORT — DO NOT USE\n"
        "Prepared by: J. Hansen, 2019\n"
        "HHV assumed: 19.8 MJ/kg (incorrect basis)\n"
        "Efficiency assumed: 75%\n"
        "This report used outdated EN standards.\n"
    ),
    "archive/templates/report_template_v1.json": json.dumps({
        "project": "TEMPLATE",
        "feedstock": {},
        "plant_sizing": {},
        "pellet_quality": {},
        "notes": "This is a generic template only. Do not submit as final."
    }, indent=2),
    "config/project_registry.json": json.dumps({
        "active_projects": ["pellet_plant_alpha", "biomass_audit"],
        "archived": ["pellet_feasibility_2019"],
        "last_updated": "2024-01-15"
    }, indent=2),
    "logs/tool_access.log": (
        "2024-01-10 09:12:33 — script.sh intro\n"
        "2024-01-10 09:15:01 — script.sh feedstocks\n"
        "2024-01-11 14:22:18 — script.sh sizing\n"
    ),
    "config/units_convention.txt": (
        "Internal convention:\n"
        "  Energy: MJ/kg (heating values), MW (plant capacity)\n"
        "  Mass: tonnes (t), kg\n"
        "  Volume: m³\n"
        "  Temperature: °C\n"
    ),
    "archive/templates/calculation_scratch.txt": (
        "Draft calc attempt (UNVERIFIED):\n"
        "Fuel = 8 / (18 * 0.82) = ??? t/h\n"
        "This used wrong HHV — recalculate with actual tool output.\n"
    ),
}

for rel_path, content in distractors.items():
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        f.write(content)

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")