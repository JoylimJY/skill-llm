import os
import json
import csv
import random

random.seed(42)

workspace = "/workspace"

# Create a deeply nested directory structure with distractor files
dirs = [
    "project_alpha/cost_estimation/legacy_exports",
    "project_alpha/cost_estimation/approved",
    "project_alpha/bim_models/ifc_exports",
    "project_alpha/bim_models/rvt_backups",
    "project_alpha/documents/specs",
    "project_alpha/documents/contracts",
    "tools/converters",
    "tools/validators",
    "archive/2021/Q3",
    "archive/2022/Q1",
    "standards/masterformat",
    "standards/uniclass",
    "standards/ifc4",
    "scratch",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---

# 1. Old IFC mapping attempt (wrong format, do not use)
with open(os.path.join(workspace, "project_alpha/bim_models/ifc_exports/old_ifc_mapping.json"), "w") as f:
    json.dump({"note": "deprecated IFC mapping from 2021, do not use", "fields": []}, f, indent=2)

# 2. A fake README that is misleading
with open(os.path.join(workspace, "project_alpha/documents/specs/field_glossary.txt"), "w") as f:
    f.write("Field glossary (draft)\n")
    f.write("element_category: the broad category of construction element\n")
    f.write("trade_code: internal trade classification code\n")
    f.write("material_class: type of raw material used\n")
    f.write("activity_desc: description of construction activity\n")
    f.write("cost_center: financial cost center ID\n")

# 3. A half-filled MasterFormat cheat sheet (partial, misleading)
with open(os.path.join(workspace, "standards/masterformat/mf_cheatsheet.txt"), "w") as f:
    f.write("MasterFormat Divisions (partial)\n")
    f.write("Division 03 - Concrete\n")
    f.write("Division 05 - Metals\n")
    f.write("Division 08 - Openings\n")
    # Note: this is intentionally incomplete and slightly wrong (08 is Openings, not Doors and Windows exactly)

# 4. A bogus Python script that does nothing useful
with open(os.path.join(workspace, "tools/converters/legacy_converter.py"), "w") as f:
    f.write("# Legacy converter - DEPRECATED\n")
    f.write("# This script was used to convert to IFC 2x3\n")
    f.write("import sys\nprint('Converter disabled')\n")

# 5. A distractor CSV with random project data
with open(os.path.join(workspace, "archive/2022/Q1/project_snapshot.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "name", "value", "unit"])
    for i in range(20):
        writer.writerow([i, f"element_{i}", random.randint(100, 9999), random.choice(["m2","m3","pcs","kg"])])

# 6. Fake validator output
with open(os.path.join(workspace, "tools/validators/last_validation_run.log"), "w") as f:
    f.write("[2022-11-03 14:22:01] Validation started\n")
    f.write("[2022-11-03 14:22:03] 47 elements checked\n")
    f.write("[2022-11-03 14:22:03] 3 warnings, 0 errors\n")
    f.write("[2022-11-03 14:22:03] Validation complete\n")

# 7. Empty approved folder placeholder
with open(os.path.join(workspace, "project_alpha/cost_estimation/approved/.gitkeep"), "w") as f:
    f.write("")

# 8. A contract document distractor
with open(os.path.join(workspace, "project_alpha/documents/contracts/contract_summary.txt"), "w") as f:
    f.write("Project Alpha - Construction Contract Summary\n")
    f.write("Client: Meridian Development Corp\n")
    f.write("Contractor: BuildTech Solutions Ltd\n")
    f.write("Contract Value: $4,250,000\n")
    f.write("Start Date: 2023-03-01\n")
    f.write("End Date: 2024-09-30\n")

# 9. A scratch file with random notes
with open(os.path.join(workspace, "scratch/notes.txt"), "w") as f:
    f.write("TODO: check if concrete slabs map to division 03 or 32\n")
    f.write("Ask John about the HVAC zone naming convention\n")
    f.write("Uniclass might be better but client uses MasterFormat\n")

# 10. Distractor standards file
with open(os.path.join(workspace, "standards/ifc4/ifc4_entity_list.txt"), "w") as f:
    f.write("IfcWall\nIfcSlab\nIfcBeam\nIfcColumn\nIfcDoor\nIfcWindow\nIfcRoof\nIfcStair\nIfcSpace\nIfcBuildingStorey\n")

# 11. Distractor uniclass file
with open(os.path.join(workspace, "standards/uniclass/uniclass2015_excerpt.txt"), "w") as f:
    f.write("Ss_25 - Wall Systems\nSs_30 - Roof Systems\nSs_32 - Floor Systems\n")

# --- THE ACTUAL PROBLEM INPUT ---

# The legacy construction project schema: messy field names with sample values
# This is what the agent must load and map to MasterFormat
legacy_schema_raw = {
    "element_category": ["concrete slab", "reinforced concrete", "masonry block"],
    "opening_type": ["door", "window", "glazing"],
    "structural_member": ["steel beam", "metal column", "girder"],
    "surface_finish": ["plaster finish", "paint coat", "tile"],
    "mep_system": ["plumbing", "hvac", "electrical conduit"],
    "thermal_layer": ["insulation", "vapour barrier", "membrane"],
    "trade_code": ["TC-0091", "TC-0042", "TC-0017"],      # should be unmapped
    "project_ref": ["PA-2023-001", "PA-2023-002"],         # should be unmapped
    "wood_framing": ["timber joist", "wood stud", "lumber"],
}

# Save as a JSON file that the agent must read and process
with open(os.path.join(workspace, "project_alpha/cost_estimation/legacy_exports/legacy_schema.json"), "w") as f:
    json.dump(legacy_schema_raw, f, indent=2)

# Also provide the list of custom mappings the agent must add manually (as a plain text specification)
# These represent fields the auto-mapper won't confidently resolve
custom_mapping_spec = """MANUAL MAPPING REQUIREMENTS
===========================
The following fields from our legacy schema could not be automatically resolved
and must be manually linked to MasterFormat divisions for the cost estimation team.

1. Field: "trade_code"
   -> Maps to MasterFormat Division "09" (Finishes)
   -> Relationship type: related
   -> Note: "Internal trade codes loosely align with finishing works"

2. Field: "project_ref"
   -> Maps to MasterFormat Division "03" (Concrete)
   -> Relationship type: related
   -> Note: "Project references are for concrete works in Phase 1"

Please apply these manual mappings AFTER running the automated mapping,
then export the complete mapping catalog and generate the summary report.
"""

with open(os.path.join(workspace, "project_alpha/cost_estimation/legacy_exports/manual_mapping_spec.txt"), "w") as f:
    f.write(custom_mapping_spec)

print("Workspace generated successfully.")
print(f"Input schema: project_alpha/cost_estimation/legacy_exports/legacy_schema.json")
print(f"Manual spec: project_alpha/cost_estimation/legacy_exports/manual_mapping_spec.txt")