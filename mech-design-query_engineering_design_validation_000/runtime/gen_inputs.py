import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested distractor directory structure
dirs = [
    "project/gearbox_design/drawings",
    "project/gearbox_design/calculations",
    "project/gearbox_design/bom",
    "project/motor_specs/datasheets",
    "project/motor_specs/test_reports",
    "project/procurement/vendors",
    "project/procurement/quotes",
    "project/quality/inspection_records",
    "project/quality/nonconformance",
    "archive/old_designs/2021",
    "archive/old_designs/2022",
    "tools/scripts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files with plausible but irrelevant content
distractors = {
    "project/gearbox_design/drawings/output_shaft_rev3.dxf": "AUTOCAD DXF R12\nENTITIES\nLINE\n0,0,0\n100,0,0\nENDSEC\nEOF",
    "project/gearbox_design/drawings/housing_rev2.dxf": "AUTOCAD DXF R12\nENTITIES\nCIRCLE\n0,0,0\n50\nENDSEC\nEOF",
    "project/gearbox_design/bom/gearbox_bom_v4.csv": "PartNo,Description,Qty,Material\nGB001,Deep Groove Ball Bearing 6208,2,52100 Steel\nGB002,Output Shaft,1,45# Steel\nGB003,Key 10x8x60,1,45# Steel\nGB004,Retaining Ring,2,65Mn",
    "project/gearbox_design/calculations/gear_ratio_calc.txt": "Gear Ratio Calculation\nInput speed: 1450 rpm\nOutput speed: 290 rpm\nRatio: 5:1\nModule: 3\nTeeth Z1=20, Z2=100",
    "project/motor_specs/datasheets/motor_Y2_132M.pdf.txt": "Y2-132M-4 Motor Datasheet\nPower: 7.5kW\nSpeed: 1450rpm\nFrame: 132M\nShaft diameter: 38mm",
    "project/motor_specs/test_reports/vibration_test_20230415.csv": "Freq,Amplitude\n50,0.012\n100,0.008\n150,0.021\n200,0.005",
    "project/procurement/vendors/approved_vendor_list.txt": "Vendor001: Shanghai Bearing Co.\nVendor002: Hangzhou Fastener Ltd.\nVendor003: Ningbo Steel Supply",
    "project/procurement/quotes/quote_bearings_2024Q1.json": json.dumps({"vendor": "Shanghai Bearing Co.", "items": [{"code": "6208", "price_rmb": 45.5, "lead_days": 7}]}),
    "project/quality/inspection_records/shaft_insp_20240312.csv": "InspItem,Nominal,Actual,Pass\nShaft OD,40.012,40.009,YES\nRunout,0.02,0.015,YES\nSurface Ra,0.8,0.6,YES",
    "project/quality/nonconformance/NCR_2024_003.txt": "NCR-2024-003: Key slot width out of tolerance. Found 10.12mm, tolerance H9 requires max 10.036mm. Disposition: Rework.",
    "archive/old_designs/2022/shaft_v1_deprecated.json": json.dumps({"shaft_dia": 35, "key_b": 10, "key_h": 8, "note": "DEPRECATED - do not use"}),
    "archive/old_designs/2021/tolerance_notes_old.txt": "Old standard reference (superseded):\nBearing fit: j5 (outdated)\nKeyway: H7 (outdated, now use H9)",
    "tools/scripts/check_tolerances.sh": "#!/bin/bash\necho 'Tolerance checker placeholder - not implemented'",
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# THE MAIN INPUT FILE: a messy, partially incorrect design input sheet
# Agent must read this, identify errors, look up correct values, compute, and produce shaft_design_report.json
design_input = {
    "_description": "Gearbox output shaft design input sheet - needs validation and completion",
    "_status": "DRAFT - contains placeholder and incorrect values marked with ???",
    "shaft_info": {
        "shaft_id": "OUTPUT_SHAFT_A1",
        "material": "45# steel",
        "shaft_diameter_bearing_seat_mm": 40,
        "shaft_diameter_oil_seal_mm": 32,
        "shaft_diameter_keyway_section_mm": 38,
        "transmitted_torque_Nm": 350,
        "key_type": "A-type flat key",
        "key_nominal_length_mm": 70,
        "connection_type": "static_steel"
    },
    "incomplete_fields": {
        "key_width_b_mm": "???",
        "key_height_h_mm": "???",
        "key_working_length_l_mm": "???",
        "key_stress_MPa": "???",
        "key_allowable_stress_MPa": "???",
        "key_strength_adequate": "???",
        "bearing_seat_tolerance_shaft": "???",
        "bearing_seat_tolerance_bore": "???",
        "keyway_slot_tolerance_shaft": "???",
        "keyway_slot_tolerance_hub": "???",
        "ra_bearing_seat_um": "???",
        "ra_oil_seal_um": "???",
        "ra_keyway_flank_um": "???",
        "ra_shaft_step_shoulder_um": "???",
        "bearing_seat_roundness_mm": "???",
        "oil_seal_circular_runout_mm": "???",
        "bearing_recommended_type": "???",
        "bearing_recommended_code": "???"
    },
    "intentionally_wrong_fields_to_correct": {
        "NOTE": "The following values were filled in by an intern and are WRONG. Correct them in the output.",
        "wrong_key_b": 14,
        "wrong_key_h": 9,
        "wrong_bearing_fit_shaft": "h6",
        "wrong_keyway_shaft_tolerance": "H7",
        "wrong_ra_bearing_seat": 1.6,
        "wrong_comment": "Bearing fit h6 is for housing location, not shaft bearing seat"
    }
}

with open(os.path.join(workspace, "project/gearbox_design/calculations/shaft_design_input.json"), "w", encoding="utf-8") as f:
    json.dump(design_input, f, indent=2, ensure_ascii=False)

print("Workspace generated successfully.")
print(f"Main input file: {workspace}/project/gearbox_design/calculations/shaft_design_input.json")