import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))
workspace.mkdir(parents=True, exist_ok=True)

# ─── Realistic distractor directory structure ───────────────────────────────

dirs = [
    "greenhouse/sector_a/tomato",
    "greenhouse/sector_b/pepper",
    "greenhouse/sector_c/lettuce",
    "seed_inventory/lot_2023",
    "seed_inventory/lot_2024",
    "reports/quarterly",
    "reports/archive",
    "protocols/internal",
    "protocols/external",
    "suppliers/vendor_alpha",
    "suppliers/vendor_beta",
    "scripts",                    # ← skill scripts live here
    "config",
    "logs",
    "temp",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ────────────────────────────────────────────────────────

distractors = {
    "greenhouse/sector_a/tomato/planting_log_2023.csv": (
        "date,rows,plants,variety\n"
        "2023-03-15,10,200,Beefsteak\n"
        "2023-04-01,8,160,Cherry\n"
    ),
    "greenhouse/sector_b/pepper/humidity_records.txt": (
        "Week 1: avg 68% RH\nWeek 2: avg 71% RH\nWeek 3: avg 65% RH\n"
    ),
    "greenhouse/sector_c/lettuce/yield_summary.txt": (
        "Q1 2024 yield: 1,200 kg\nQ2 2024 yield: 1,450 kg\n"
    ),
    "seed_inventory/lot_2023/manifest.csv": (
        "lot_id,crop,weight_kg,supplier\n"
        "L2023-001,tomato,5.0,VendorAlpha\n"
        "L2023-002,pepper,3.2,VendorBeta\n"
        "L2023-003,lettuce,1.8,VendorAlpha\n"
    ),
    "seed_inventory/lot_2024/incoming_lots.csv": (
        "lot_id,crop,weight_kg,received_date,target_transplant\n"
        "L2024-010,tomato,6.0,2024-01-15,2024-04-20\n"
        "L2024-011,lettuce,2.5,2024-01-20,2024-03-30\n"
        "L2024-012,pepper,4.0,2024-01-22,2024-05-10\n"
    ),
    "reports/quarterly/Q3_2023_summary.txt": (
        "Q3 2023: Overall germination rates within acceptable range.\n"
        "Tomato lot L2023-001: 88% germination\n"
        "Pepper lot L2023-002: 79% germination\n"
    ),
    "reports/archive/old_protocol_notes.txt": (
        "Legacy protocol: 50 seeds per tray, 3 replicates, 7 days.\n"
        "Note: This was superseded by current ISTA guidelines.\n"
    ),
    "protocols/internal/sop_v2.txt": (
        "Internal SOP version 2.0\n"
        "Last updated: 2022-11-01\n"
        "Status: DRAFT — pending external validation\n"
    ),
    "protocols/external/placeholder.txt": (
        "External protocol documents to be filed here.\n"
    ),
    "suppliers/vendor_alpha/contact.txt": (
        "Vendor Alpha Seeds\nContact: seeds@vendor-alpha.example.com\nPhone: 555-0100\n"
    ),
    "suppliers/vendor_beta/pricing_2024.csv": (
        "crop,price_per_kg,min_order_kg\n"
        "tomato,120,2\n"
        "pepper,95,3\n"
        "lettuce,45,5\n"
    ),
    "config/env_defaults.sh": (
        "#!/usr/bin/env bash\n"
        "# Default environment settings — NOT for germination data\n"
        "export LOG_LEVEL=INFO\n"
        "export MAX_RETRIES=3\n"
    ),
    "logs/system.log": (
        "[2024-01-10 08:00:01] INFO  System startup OK\n"
        "[2024-01-10 08:00:05] INFO  Scripts directory mounted\n"
        "[2024-01-15 14:23:11] WARN  GERMINATION_DIR not set, using default\n"
    ),
    "temp/scratch.txt": (
        "TODO: run germination checks on lot L2024-010, L2024-011, L2024-012\n"
        "Ask Maria about ISTA sample sizes\n"
    ),
}

for rel_path, content in distractors.items():
    (workspace / rel_path).write_text(content)

# ─── The skill's scripts/script.sh (stub that outputs realistic content) ─────
# The SKILL.md states "All scripts mentioned in the SKILL.md already exist."
# We create a realistic, information-rich script that the agent must interrogate.

script_content = r"""#!/usr/bin/env bash
# germination skill v1.0.0 — BytesAgain

set -euo pipefail

DATA_DIR="${GERMINATION_DIR:-$HOME/.germination}"
CMD="${1:-help}"

case "$CMD" in

intro)
cat <<'EOF'
=== GERMINATION — OVERVIEW ===
Germination is the process by which a seed develops into a seedling.
Key phases:
  1. Imbibition    — seed absorbs water (moisture content rises to 40–60%)
  2. Activation    — metabolic processes resume, enzymes activate
  3. Radicle emergence — primary root breaks seed coat (visible germination)

Key factors: temperature, moisture, oxygen, light (crop-dependent)
Optimal germination requires all four factors in correct balance.
EOF
;;

conditions)
cat <<'EOF'
=== OPTIMAL GERMINATION CONDITIONS ===
Crop        | Min °C | Opt °C | Max °C | Moisture % | Light
------------|--------|--------|--------|------------|------
Tomato      |    10  |   22   |   35   |    70–80   | Dark
Pepper      |    16  |   26   |   32   |    75–85   | Dark
Lettuce     |     2  |   18   |   25   |    60–70   | Light (some cvs)
Carrot      |     7  |   20   |   30   |    65–75   | Dark
Cucumber    |    16  |   25   |   35   |    70–80   | Dark
Basil       |    18  |   24   |   30   |    70–80   | Dark
Onion       |     2  |   20   |   35   |    65–75   | Dark
Spinach     |     2  |   16   |   24   |    60–70   | Light
Brassica    |     7  |   20   |   30   |    65–75   | Dark
Celery      |    10  |   20   |   25   |    70–80   | Light
EOF
;;

dormancy)
cat <<'EOF'
=== SEED DORMANCY & BREAKING METHODS ===
Dormancy types:
  - Physical (hard seed coat): scarification — mechanical or acid
  - Physiological (embryo dormancy): cold stratification (2–5°C for 4–12 weeks)
  - Morphological (underdeveloped embryo): warm stratification or GA3 treatment
  - Combinational: sequential warm + cold stratification

Methods:
  Scarification:   nick, sand, sandpaper, hot water soak (85°C, 5–10 min)
  Cold strat:      moist medium, 4°C, species-dependent duration
  Warm strat:      25–30°C, 4–8 weeks before cold treatment
  Leaching:        running water, 12–24 hours (inhibitor removal)
  KNO3 soak:       0.2% solution, 24 hr (light-sensitive seeds)
  GA3:             gibberellic acid 100–500 ppm soak 24 hr
EOF
;;

testing)
cat <<'EOF'
=== GERMINATION TESTING PROTOCOLS ===
ISTA (International Seed Testing Association) Standard Rules:
  - Minimum sample size: 400 seeds per lot (4 replicates × 100 seeds each)
  - Substrate: paper (TP, BP, S), sand, or soil — crop-specific
  - Evaluation intervals: first count + final count (days per crop)
  - Germination percentage: (normal seedlings / total seeds) × 100
  - Acceptable commercial threshold: 85% for most vegetable crops
  - Pure seed analysis required before germination test
  - Temperature: crop-specific; alternating temp regimes for some crops

Paper Towel Test (informal):
  - 10 seeds on moist paper towel, folded, placed in 20–25°C
  - Count normal sprouts at 7–10 days
  - Viability estimate: (sprouted / 10) × 100

Tetrazolium Test (TZ):
  - Soak seed 16–18 hr, bisect longitudinally
  - Immerse in 1% TZ solution, 30–40°C, 2–4 hr in dark
  - Living cells stain red; dead tissue remains unstained
  - Quick viability indicator (not germination per se)

ISTA First Count Days (selected crops):
  Tomato:   first count day 7,  final count day 14
  Pepper:   first count day 7,  final count day 14
  Lettuce:  first count day 4,  final count day 7
  Carrot:   first count day 7,  final count day 14
  Cucumber: first count day 4,  final count day 8

Minimum germination standards (commercial seed lots):
  Tomato:   85%
  Pepper:   80%
  Lettuce:  80%
  Carrot:   65%
  Cucumber: 85%
EOF
;;

crops)
cat <<'EOF'
=== CROP GERMINATION DATA ===
Crop        | Days to Germ | Opt Temp °C | Sow Depth cm | Bench Rate %
------------|--------------|-------------|--------------|-------------
Tomato      |      5–10    |    22–26    |      0.5     |    85–95
Pepper      |      7–14    |    24–28    |      0.5     |    80–90
Lettuce     |      2–8     |    15–20    |      0.3     |    80–90
Carrot      |      7–21    |    18–22    |      0.5     |    65–75
Cucumber    |      3–7     |    24–28    |      1.0     |    85–95
Basil       |      5–10    |    22–25    |      0.3     |    85–90
Onion       |      7–14    |    18–24    |      1.0     |    70–80
Spinach     |      7–14    |    10–16    |      1.5     |    60–75
Brassica    |      4–7     |    18–24    |      0.5     |    85–92
Celery      |     14–21    |    18–22    |    surface   |    70–80
EOF
;;

problems)
cat <<'EOF'
=== GERMINATION TROUBLESHOOTING ===
Problem              | Likely Cause                | Remedy
---------------------|-----------------------------|--------------------------
No germination       | Dormancy not broken         | Scarify / stratify
                     | Temperature too low/high    | Adjust to optimal range
                     | Seeds too old / dead        | Run TZ or paper towel test
                     | Sown too deep               | Re-sow at correct depth
Damping off          | Fungal pathogen (Pythium)   | Improve air circulation
                     | Overwatering                | Reduce moisture, use fungicide drench
Uneven emergence     | Poor seed-to-soil contact   | Firm seedbed, improve sowing
                     | Soil crust formation        | Use sandy medium, mist lightly
Low germination rate | Low seed viability          | Replace lot or pre-soak
                     | Pathogen-infected lot       | Seed treatment (thiram/captan)
                     | Incorrect temperature       | Check thermometer calibration
Seedling abnormality | Nutrient deficiency         | Use balanced starter feed
                     | Herbicide residue           | Flush medium
EOF
;;

enhancement)
cat <<'EOF'
=== SEED ENHANCEMENT TECHNIQUES ===
Priming:
  - Hydropriming: soak in water (controlled hydration), then re-dry
  - Osmopriming: PEG 6000 solution (-1.0 to -1.5 MPa), 15–20°C, 48–72 hr
  - Halopriming: KNO3 or KH2PO4 solution
  - Biopriming: inoculate with beneficial microbes (Trichoderma, Bacillus)
  - Matric priming: solid carrier matrix + water

Pelleting:
  - Clay or diatomite coating for uniform size/weight
  - Improves precision sowing in mechanised operations

Coating:
  - Film coating: polymer film with colorant and/or active ingredient
  - Includes fungicide, insecticide, rhizobium, micronutrients

Benefits: faster, more uniform emergence; improved stand establishment
EOF
;;

schedule)
cat <<'EOF'
=== GERMINATION & TRANSPLANT SCHEDULING ===
Formula:
  Sow Date = Transplant Date − (Days to Germination + Seedling Growth Days + Hardening-off Days)

Hardening-off periods (standard):
  Tomato:   7 days
  Pepper:   7 days
  Lettuce:  4 days
  Carrot:   N/A (direct sow)
  Cucumber: 5 days
  Basil:    5 days
  Onion:    7 days
  Spinach:  4 days
  Brassica: 5 days
  Celery:   7 days

Typical seedling growth (transplant stage) days from germination:
  Tomato:   35–42 days
  Pepper:   42–49 days
  Lettuce:  21–28 days
  Cucumber: 14–21 days
  Basil:    21–28 days
  Onion:    42–49 days
  Brassica: 28–35 days
  Celery:   56–63 days

Note: Use MIDPOINT of ranges for planning.
      Sow Date must be a calendar date (YYYY-MM-DD).
EOF
;;

help)
cat <<'EOF'
=== GERMINATION SKILL — HELP ===
Usage: scripts/script.sh <command>

Commands:
  intro        Overview of germination biology
  conditions   Optimal temperature/moisture conditions by crop
  dormancy     Dormancy types and breaking methods
  testing      ISTA and informal germination testing protocols
  crops        Crop-specific germination data
  problems     Troubleshooting guide
  enhancement  Seed enhancement techniques
  schedule     Scheduling — sow date calculation
  help         This help text
  version      Show version

Environment:
  GERMINATION_DIR   Data directory (default: ~/.germination/)
EOF
;;

version)
echo "germination v1.0.0 — BytesAgain (bytesagain.com)"
;;

*)
echo "Unknown command: $CMD" >&2
echo "Run: scripts/script.sh help" >&2
exit 1
;;
esac
"""

(workspace / "scripts" / "script.sh").write_text(script_content)

# ─── Task input: the seed lot assessment request ─────────────────────────────

task_brief = {
    "assessment_id": "GH2024-AUDIT-03",
    "requested_by": "Maria Chen, Head of Greenhouse Operations",
    "date_issued": "2024-01-25",
    "lots_to_assess": [
        {
            "lot_id": "L2024-010",
            "crop": "tomato",
            "target_transplant_date": "2024-04-20",
            "observed_germination_pct": 87,
            "notes": "Lot received in good condition. No visible damage."
        },
        {
            "lot_id": "L2024-011",
            "crop": "lettuce",
            "target_transplant_date": "2024-03-30",
            "observed_germination_pct": 76,
            "notes": "Some seeds appear shrivelled. Possible age issue."
        },
        {
            "lot_id": "L2024-012",
            "crop": "pepper",
            "target_transplant_date": "2024-05-10",
            "observed_germination_pct": 82,
            "notes": "Uniform appearance. Minor inconsistency in emergence timing."
        }
    ],
    "instruction": "Produce a structured audit report as seed_lot_audit.json"
}

(workspace / "seed_inventory" / "lot_2024" / "assessment_request.json").write_text(
    json.dumps(task_brief, indent=2)
)

print("Workspace generated successfully.")
print(f"Root: {workspace}")