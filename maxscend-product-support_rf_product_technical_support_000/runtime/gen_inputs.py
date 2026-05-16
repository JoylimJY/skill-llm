import os
import random
import json
import csv

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure ──────────────────────────────────────────────
dirs = [
    "project/rf_design/schematics",
    "project/rf_design/simulation",
    "project/rf_design/bom",
    "project/rf_design/test_data",
    "project/system/specs",
    "project/system/architecture",
    "project/vendor_docs/competitor",
    "project/vendor_docs/internal",
    "project/meeting_notes",
    "project/pcb_layout/gerbers",
    "project/pcb_layout/guidelines",
    "archive/old_designs/2022",
    "archive/old_designs/2023",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────

# 1. Old BOM with wrong/irrelevant parts
with open(os.path.join(workspace, "project/rf_design/bom/old_bom_v1.csv"), "w") as f:
    f.write("RefDes,Manufacturer,Part Number,Description,Qty\n")
    f.write("SW1,Skyworks,SKY13351,SP4T Switch,1\n")
    f.write("LNA1,Qorvo,QPL9503,Low Noise Amplifier,1\n")
    f.write("F1,Murata,SAFEA1G88MA0F0A,SAW Filter,1\n")
    f.write("C1,TDK,C0402C104K5RAC,100nF Decoupling,4\n")

# 2. Simulation result (distractor, wrong band)
with open(os.path.join(workspace, "project/rf_design/simulation/band3_sim_results.txt"), "w") as f:
    f.write("Simulation: Band 3 (1800MHz) LNA Chain\n")
    f.write("NF = 1.8dB\n")
    f.write("Gain = 14.2dB\n")
    f.write("This is a legacy simulation for Band 3, not relevant to current 5G NR project.\n")

# 3. Architecture diagram text
with open(os.path.join(workspace, "project/system/architecture/rx_chain_arch.txt"), "w") as f:
    f.write("5G NR Receive Chain Architecture\n")
    f.write("Antenna → Antenna Switch → Band Filter → LNA → Mixer\n")
    f.write("Target Bands: n77 (3300-4200MHz), n78 (3300-3800MHz)\n")
    f.write("Note: This is a conceptual diagram only, component selection TBD.\n")

# 4. Competitor analysis (distractor)
with open(os.path.join(workspace, "project/vendor_docs/competitor/competitor_analysis.txt"), "w") as f:
    f.write("Competitor Analysis - RF Front End Suppliers\n")
    f.write("Supplier A: Skyworks - Strong in PA, limited 5G NR coverage\n")
    f.write("Supplier B: Qorvo - Good PAMiD solutions\n")
    f.write("Supplier C: Maxscend - Local supplier, evaluating feasibility\n")
    f.write("Decision: Evaluate Maxscend for cost optimization\n")

# 5. PCB layout notes
with open(os.path.join(workspace, "project/pcb_layout/guidelines/rf_layout_rules.txt"), "w") as f:
    f.write("General RF PCB Layout Rules\n")
    f.write("- Keep RF traces short\n")
    f.write("- Use ground vias frequently\n")
    f.write("- Separate TX and RX paths\n")
    f.write("- 50 ohm controlled impedance on all RF lines\n")

# 6. Meeting notes
with open(os.path.join(workspace, "project/meeting_notes/kickoff_2024_01.txt"), "w") as f:
    f.write("Project Kickoff Meeting - 2024-01-15\n")
    f.write("Attendees: RF Lead, Systems Engineer, PM\n")
    f.write("Action: Evaluate Maxscend 5G NR FEM components\n")
    f.write("Deadline: Prototype ready by Q2 2024\n")
    f.write("Budget: Component cost target <$0.50 per unit\n")

# 7. Old schematic notes
with open(os.path.join(workspace, "project/rf_design/schematics/v1_notes.txt"), "w") as f:
    f.write("Schematic v1 Notes\n")
    f.write("- Used MXD8641 for antenna switch but had isolation issues\n")
    f.write("- LNA placement caused coupling\n")
    f.write("- Filter not yet selected\n")

# 8. Archive files
with open(os.path.join(workspace, "archive/old_designs/2022/band1_design.txt"), "w") as f:
    f.write("2022 Band 1 Design Archive\n")
    f.write("MXD8641 SP4T switch used for Band 1\n")
    f.write("MXD1801 LNA - Band 1 700-1000MHz\n")
    f.write("MXF2102 Filter - Band 1 TX\n")

with open(os.path.join(workspace, "archive/old_designs/2023/band3_design.txt"), "w") as f:
    f.write("2023 Band 3 Design Archive\n")
    f.write("Cascade NF achieved: 1.9dB\n")

# 9. System specs (partial, for context)
with open(os.path.join(workspace, "project/system/specs/5g_system_requirements.txt"), "w") as f:
    f.write("5G NR System Requirements - CONFIDENTIAL\n")
    f.write("Target bands: n77 (3300-4200 MHz), n78 (3300-3800 MHz)\n")
    f.write("Platform: Android flagship smartphone\n")
    f.write("Volume: 5M units/year\n")

# 10. Gerbers placeholder
with open(os.path.join(workspace, "project/pcb_layout/gerbers/README_gerbers.txt"), "w") as f:
    f.write("Gerber files to be added after schematic freeze.\n")

# 11. Vendor internal notes
with open(os.path.join(workspace, "project/vendor_docs/internal/maxscend_intro.txt"), "w") as f:
    f.write("Maxscend (卓胜微) - Internal Evaluation Notes\n")
    f.write("Company: Leading domestic RF front-end chip designer\n")
    f.write("Products: RF Switch, LNA, SAW/BAW Filter, RF Module, PA\n")
    f.write("Contact: FAE support engaged\n")

# ── THE REAL PROBLEM FILES ───────────────────────────────────────────

# 12. Requirements CSV (messy, some fields incomplete)
req_data = [
    ["Parameter", "Requirement", "Unit", "Notes"],
    ["Target Band", "n77/n78", "-", "3300-4200MHz for n77; 3300-3800MHz for n78"],
    ["Cascade NF Budget", "3.5", "dB", "Maximum allowed total receive chain NF"],
    ["Min Gain", "12", "dB", "After filter + switch + LNA"],
    ["Antenna Switch Type", "SP4T", "-", "Single antenna input, 4 output paths"],
    ["Switch IL Requirement", "0.5", "dB", "Maximum insertion loss for RX chain switch"],
    ["LNA Frequency Coverage", "3300-4200", "MHz", "Must cover full n77 band"],
    ["Filter Center Frequency", "3500", "MHz", "5G n78 filter required"],
    ["PCB Area Constraint", "discrete", "-", "Discrete components acceptable, module preferred if available"],
    ["Supply Voltage", "3.0", "V", "Available VCC"],
    ["Control Interface", "GPIO", "-", "No MIPI available on this platform"],
    ["ACLR Requirement", "TBD", "-", "PA spec, not in scope for this task"],
    ["Cost Target", "0.50", "USD", "Per unit BOM cost"],
]

with open(os.path.join(workspace, "project/system/specs/rx_chain_requirements.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(req_data)

# 13. Messy test log with symptoms (realistic RF lab output)
test_log = """=== RF Receive Chain Test Log ===
Date: 2024-03-12
Engineer: Wang Lei
Board: Proto-v2, n77/n78 evaluation board
Components Under Test: TBD Maxscend selection

--- Test Setup ---
VNA: Keysight E5063A
Noise Figure Analyzer: Keysight N8973B
Test frequency: 3500 MHz
Temp: 25C

--- Test Results ---
[PASS] S11 (Switch Input): -18.2 dB @ 3.5GHz (target: < -10dB)
[FAIL] Noise Figure (System): 4.8 dB (target: <= 3.5 dB) *** OUT OF SPEC ***
[PASS] System Gain: 13.1 dB (target: >= 12 dB)
[PASS] Switch Isolation RF1-RF2: 24.3 dB (target: > 20dB)
[FAIL] LNA NF contribution: appears elevated, suspect input matching issue
[INFO] Filter insertion loss measured: 1.5 dB @ 3.5GHz (within spec)
[INFO] Switch insertion loss measured: 0.48 dB (within spec)
[WARN] Supply voltage measured 2.85V (nominal 3.0V, slight droop under load)
[INFO] Input trace length: ~18mm before LNA input port
[INFO] Via count near LNA GND pads: 3 vias (may be insufficient)
[FAIL] Output return loss LNA: -8.1 dB (target: < -10 dB)

--- Engineer Notes ---
NF failure is primary concern. Gain is OK so the components are powered.
The LNA might not be properly matched. Also noticed long input trace routing.
Need troubleshooting guidance from Maxscend FAE.
Supply voltage droop also suspicious.
Requesting: component selection confirmation + cascade NF calculation + fault diagnosis.

--- Raw NF Sweep (3.3-3.8 GHz) ---
Freq(GHz), NF(dB)
3.30, 4.6
3.35, 4.7
3.40, 4.75
3.45, 4.82
3.50, 4.80
3.55, 4.85
3.60, 4.90
3.65, 4.88
3.70, 4.95
3.75, 4.91
3.80, 4.87
"""

with open(os.path.join(workspace, "project/rf_design/test_data/proto_v2_test_log.txt"), "w") as f:
    f.write(test_log)

# 14. Partial BOM template that agent needs to fill/reference (but this is the OUTPUT they create)
# We do NOT create the output file - agent must create it
# But we create a template hint file showing expected format
bom_template_note = """BOM Template Note (for reference only):
The final technical report should be saved as: feasibility_report.json
It must contain component selections, cascade NF calculation, and fault diagnosis.
No further format details are provided here.
"""
with open(os.path.join(workspace, "project/rf_design/bom/bom_template_note.txt"), "w") as f:
    f.write(bom_template_note)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")