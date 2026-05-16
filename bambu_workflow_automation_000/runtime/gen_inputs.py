import os
import json
import random
import struct
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deep directory structure with distractor files ---

dirs = [
    "shift_handoff/morning",
    "shift_handoff/night",
    "shift_handoff/archive",
    "printer_assets/models/approved",
    "printer_assets/models/draft",
    "printer_assets/profiles/pla",
    "printer_assets/profiles/abs",
    "printer_assets/profiles/petg",
    "maintenance_logs/2024",
    "maintenance_logs/2025",
    "calibration_records",
    "filament_inventory",
    "failed_prints",
    "network_config/old",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

distractors = {
    "shift_handoff/morning/handoff_template.txt": "Shift Handoff Template\n======================\nPrinter status: [ ] OK  [ ] Needs attention\nJobs completed: \nNotes: \n",
    "shift_handoff/archive/2025-01-15_handoff.txt": "Shift completed. Printed bracket_v3.3mf successfully. No issues.\nAMS slots 0,1,2 used. Slot 3 empty.",
    "shift_handoff/archive/2025-01-16_handoff.txt": "Printer needed cooldown after long run. PLA stuck in slot 2, cleared manually.",
    "maintenance_logs/2024/Q4_maintenance.txt": "- Replaced nozzle (0.4mm)\n- Cleaned AMS gears\n- Recalibrated bed (all 49 points)\n- Updated firmware to 01.07.00.00",
    "maintenance_logs/2025/inspection_feb.txt": "Visual inspection: OK. No clogging. Filament paths clean.",
    "calibration_records/last_bed_cal.json": json.dumps({"date": "2025-02-10", "method": "auto", "points": 49, "max_deviation": 0.12, "result": "pass"}, indent=2),
    "calibration_records/vibration_log.txt": "Vibration calibration: X axis OK, Y axis slight resonance at 180mm/s, compensated.",
    "filament_inventory/stock.csv": "brand,color,type,weight_g,slot\nBambuLab,White,PLA Basic,850,0\nBambuLab,Black,PLA Basic,920,1\nBambuLab,Grey,PLA Matte,780,2\nBambuLab,EMPTY,EMPTY,0,3\n",
    "filament_inventory/reorder_list.txt": "- PLA Basic White x2\n- PETG Transparent x1\n- ABS Black x1",
    "failed_prints/2025-02-12_failure_report.txt": "Job: gear_housing_v2.3mf\nFailure mode: Layer adhesion failure at Z=42mm\nFilament: PLA Matte slot 2\nTemps: nozzle 215, bed 65\nAction: Reprinting with nozzle 220",
    "failed_prints/clog_event_jan.txt": "Partial clog detected mid-print. Purged 80mm, resumed OK.",
    "printer_assets/profiles/pla/standard_pla.txt": "Layer height: 0.2mm\nInfill: 15%\nSupports: None\nNozzle temp: 210\nBed temp: 60\nCooling: 100%",
    "printer_assets/profiles/abs/standard_abs.txt": "Layer height: 0.2mm\nInfill: 20%\nSupports: Auto\nNozzle temp: 260\nBed temp: 100\nCooling: 0%",
    "printer_assets/profiles/petg/standard_petg.txt": "Layer height: 0.2mm\nInfill: 20%\nSupports: Auto\nNozzle temp: 240\nBed temp: 80\nCooling: 50%",
    "network_config/old/printer_ip_history.txt": "2024-11-01: 192.168.1.55 (old router)\n2024-12-15: 192.168.1.88 (after router swap)\n2025-01-03: 192.168.1.101 (current)\n",
    "network_config/old/deprecated_setup.sh": "#!/bin/bash\n# OLD METHOD - DO NOT USE\n# octoprint connect --host 192.168.1.101 --port 80\necho 'deprecated'",
    "printer_assets/models/draft/prototype_v1.txt": "Draft model - not approved for printing",
    "printer_assets/models/draft/bracket_test_geometry.txt": "Vertices: 2048, Faces: 4096, Volume: 12.4cc",
    "maintenance_logs/2025/nozzle_wear_check.txt": "Measured nozzle diameter: 0.41mm (within tolerance). No replacement needed.",
}

for relpath, content in distractors.items():
    fpath = workspace / relpath
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# --- THE REAL PROBLEM FILES ---

# 1. Shift handoff notes with printer credentials and job details
handoff_notes = """NIGHT SHIFT HANDOFF NOTES - 2025-03-10
=======================================
LEFT BY: Maria Chen (Night Shift Lead)
FOR:     Day shift team

PRINTER CREDENTIALS (Bambu X1C - Lab Unit #3)
----------------------------------------------
IP Address:    192.168.10.47
Serial Number: 01S09C382900001
LAN Code:      12345678

STATUS AT END OF SHIFT:
  - Printer cooled down and lights off
  - AMS loaded and ready
  - SD card cleared of old jobs

PENDING PRINT JOB:
  - File: enclosure_bracket_v4.3mf (in printer_assets/models/approved/)
  - Material: PLA Basic (White) - slot 0 in AMS
  - USE STANDARD PLA PROFILE for temps

TASKS FOR DAY SHIFT:
  1. Connect to the printer using the credentials above
  2. Verify connection is working
  3. Set temperatures to standard PLA profile before starting
  4. Upload and start the pending print job (use the all-in-one upload+print command)
  5. Check AMS status and confirm slot 0 is active
  6. Record everything in a session report file called print_session_report.json
     Include: printer IP, serial, which file was printed, AMS slot used, 
     temperatures set (nozzle and bed), and timestamp of session start.

NOTE: The old OctoPrint setup scripts in network_config/ are DEPRECATED. 
Use the new CLI tool documented in the lab's skill docs.
"""

(workspace / "shift_handoff/morning/todays_handoff.txt").write_text(handoff_notes)

# 2. The actual 3MF file to print (minimal valid-ish binary placeholder)
# A 3MF is a ZIP file. Let's create a minimal one.
import zipfile
import io

three_mf_path = workspace / "printer_assets/models/approved/enclosure_bracket_v4.3mf"
buf = io.BytesIO()
with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    zf.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel" Target="/3D/model.model" Id="rel0"/></Relationships>')
    zf.writestr("3D/model.model", '<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="1" type="model"><mesh><vertices><v x="0" y="0" z="0"/><v x="10" y="0" z="0"/><v x="0" y="10" z="0"/><v x="0" y="0" z="10"/></vertices><triangles><triangle v1="0" v2="1" v3="2"/><triangle v1="0" v2="1" v3="3"/><triangle v1="0" v2="2" v3="3"/><triangle v1="1" v2="2" v3="3"/></triangles></mesh></object></resources><build><item objectid="1"/></build></model>')
three_mf_path.write_bytes(buf.getvalue())

# 3. A misleading old config file (wrong credentials, should NOT be used)
old_config_dir = Path.home() / ".bambu_old"
old_config_dir.mkdir(exist_ok=True)
(old_config_dir / "config.json").write_text(json.dumps({
    "ip": "192.168.1.88",
    "serial": "OLDSERIAL00000",
    "access_code": "00000000"
}, indent=2))

# 4. An existing wrong ~/.bambu config (stale/wrong - agent must overwrite with correct setup)
bambu_config_dir = Path.home() / ".bambu"
bambu_config_dir.mkdir(exist_ok=True)
(bambu_config_dir / "config.json").write_text(json.dumps({
    "ip": "192.168.1.101",
    "serial": "STALE_SERIAL_XYZ",
    "access_code": "99999999",
    "note": "stale config from previous session"
}, indent=2))

print("Workspace generated successfully.")
print(f"Key file: {workspace}/shift_handoff/morning/todays_handoff.txt")
print(f"3MF file: {three_mf_path}")
print(f"Stale config planted at: {bambu_config_dir / 'config.json'}")