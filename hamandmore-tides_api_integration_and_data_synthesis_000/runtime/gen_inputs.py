import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# === Deep distractor directory structure ===
dirs = [
    "harbor_ops/logs/2025",
    "harbor_ops/logs/2026",
    "harbor_ops/vessel_manifests",
    "harbor_ops/maintenance/dredging",
    "harbor_ops/maintenance/buoys",
    "harbor_ops/weather_archive/raw",
    "harbor_ops/weather_archive/processed",
    "harbor_ops/tide_charts/old_format",
    "harbor_ops/tide_charts/deprecated",
    "harbor_ops/safety/reports",
    "harbor_ops/safety/templates",
    "harbor_ops/comms/vhf_logs",
    "harbor_ops/scheduling/arrivals",
    "harbor_ops/scheduling/departures",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = [
    ("harbor_ops/logs/2025/jan_incidents.txt", "Incident log: minor grounding near buoy 7. No casualties.\n"),
    ("harbor_ops/logs/2025/feb_maintenance.txt", "Routine maintenance completed on dock 3.\n"),
    ("harbor_ops/logs/2026/q1_summary.txt", "Q1 2026 summary: 342 vessel movements, 0 major incidents.\n"),
    ("harbor_ops/vessel_manifests/mv_stormrider.json", json.dumps({"vessel": "MV Stormrider", "draft_m": 4.2, "loa_m": 87.5, "flag": "NL"})),
    ("harbor_ops/vessel_manifests/mv_atlas.json", json.dumps({"vessel": "MV Atlas", "draft_m": 3.8, "loa_m": 72.0, "flag": "DE"})),
    ("harbor_ops/maintenance/dredging/schedule_2026.csv", "zone,start_date,end_date\nChannel A,2026-03-01,2026-03-15\nBerth 4,2026-04-10,2026-04-20\n"),
    ("harbor_ops/maintenance/buoys/inspection_log.txt", "Buoy 12: reflector replaced 2026-01-15\nBuoy 7: chain inspected 2026-01-22\n"),
    ("harbor_ops/weather_archive/raw/noaa_stub.json", json.dumps({"source": "NOAA stub", "note": "placeholder only, not real data"})),
    ("harbor_ops/weather_archive/processed/monthly_means.csv", "month,mean_wind_kts,mean_temp_c\n2025-01,12.3,4.1\n2025-02,14.7,3.8\n"),
    ("harbor_ops/tide_charts/old_format/tides_1990.dat", "# Legacy harmonic constants - DO NOT USE\nM2 1.23 45.6\nS2 0.87 120.3\n"),
    ("harbor_ops/tide_charts/deprecated/gauge_readings_2010.csv", "timestamp,height_m\n2010-01-01T00:00:00Z,1.23\n2010-01-01T01:00:00Z,1.45\n"),
    ("harbor_ops/safety/templates/pre_departure_checklist.txt", "1. Check tide window\n2. Verify weather\n3. Confirm crew manifest\n4. Test comms\n"),
    ("harbor_ops/comms/vhf_logs/channel16_jan2026.txt", "0800 MV Stormrider: request berth 5\n0815 Harbourmaster: approved, max draft 4.5m at HW\n"),
    ("harbor_ops/scheduling/arrivals/week07_2026.csv", "vessel,eta,berth\nMV Atlas,2026-02-16T08:00:00Z,3\nMV Stormrider,2026-02-17T14:00:00Z,5\n"),
    ("harbor_ops/scheduling/departures/week07_2026.csv", "vessel,etd,berth\nMV Atlas,2026-02-18T10:00:00Z,3\n"),
]

for rel_path, content in distractor_files:
    fpath = workspace / rel_path
    fpath.write_text(content)

# === The actual task brief (business context, no technical hints) ===
brief = {
    "task": "Coastal Safety Pre-Departure Analysis",
    "location": {
        "name": "Port of Brest, France",
        "latitude": 48.3833,
        "longitude": -4.4833
    },
    "analysis_window": {
        "start": "2026-02-15T00:00:00Z",
        "end": "2026-02-17T00:00:00Z"
    },
    "vessel": "MV Stormrider",
    "instructions": (
        "The harbor master requires a machine-readable safety assessment for MV Stormrider's departure. "
        "You must identify the single highest high-tide event at the port during the analysis window, "
        "then obtain the tide height exactly one hour before that peak, "
        "and retrieve wind and temperature conditions at the port covering the same analysis window. "
        "Compile all findings into a structured report file named 'departure_safety_report.json' "
        "and place it inside the harbor_ops/safety/reports/ directory."
    ),
    "required_output_fields": [
        "peak_high_tide",
        "pre_peak_reading",
        "weather_snapshot"
    ]
}

brief_path = workspace / "harbor_ops/safety/task_brief.json"
brief_path.write_text(json.dumps(brief, indent=2))

print("Workspace initialized.")
print(f"Task brief written to: {brief_path}")