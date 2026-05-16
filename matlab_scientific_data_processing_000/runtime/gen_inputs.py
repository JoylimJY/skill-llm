import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Distractor directory structure ──────────────────────────────────────────
dirs = [
    "project/data/raw",
    "project/data/processed",
    "project/scripts/utils",
    "project/scripts/legacy",
    "project/reports/monthly",
    "project/reports/annual",
    "project/config",
    "project/notebooks",
    "project/archive/2022",
    "project/archive/2023",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractors = {
    "project/config/station_meta.json": json.dumps({
        "station_id": "WS-042",
        "location": "Alpine Ridge",
        "elevation_m": 2340,
        "sensors": ["temperature", "humidity", "pressure", "wind_speed"]
    }, indent=2),

    "project/data/raw/README_SENSORS.txt": (
        "Raw sensor files — do not edit manually.\n"
        "Contact data team for calibration constants.\n"
    ),

    "project/scripts/legacy/old_normalize.m": (
        "% DEPRECATED — do not use\n"
        "function y = old_normalize(x)\n"
        "  y = (x - min(x)) / (max(x) - min(x));\n"
        "end\n"
    ),

    "project/scripts/utils/plot_helper.m": (
        "function plot_helper(data, title_str)\n"
        "  figure;\n"
        "  plot(data);\n"
        "  title(title_str);\n"
        "end\n"
    ),

    "project/reports/monthly/jan_summary.txt": (
        "January Summary\n"
        "Mean Temp: 3.2 C\n"
        "Max Wind: 87 km/h\n"
    ),

    "project/reports/annual/2023_annual.txt": (
        "Annual report 2023 — see processed data folder.\n"
    ),

    "project/notebooks/exploratory.txt": (
        "Exploratory analysis notes:\n"
        "- Several NaN gaps in wind_speed channel\n"
        "- Pressure sensor has outliers above 1100 hPa\n"
        "- Temperature looks clean\n"
    ),

    "project/archive/2022/backup_note.txt": "Archived 2022-12-31.\n",
    "project/archive/2023/backup_note.txt": "Archived 2023-12-31.\n",

    "project/config/thresholds.json": json.dumps({
        "temperature": {"min": -40, "max": 60},
        "humidity": {"min": 0, "max": 100},
        "pressure": {"min": 870, "max": 1084},
        "wind_speed": {"min": 0, "max": 200}
    }, indent=2),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── Core input: sensor CSV with NaN gaps ─────────────────────────────────────
# 24 hourly readings; some NaN entries scattered across channels
import math

random.seed(42)

hours = list(range(24))
temperature = [round(-5 + 8 * math.sin(h * math.pi / 12) + random.uniform(-0.5, 0.5), 2)
               for h in hours]
humidity    = [round(60 + 20 * math.cos(h * math.pi / 12) + random.uniform(-1, 1), 2)
               for h in hours]
pressure    = [round(1013 + 5 * math.sin(h * math.pi / 8) + random.uniform(-0.3, 0.3), 2)
               for h in hours]
wind_speed  = [round(max(0, 15 + 10 * math.sin(h * math.pi / 6) + random.uniform(-2, 2)), 2)
               for h in hours]

# Inject NaN at specific positions (using empty string to represent NaN in CSV)
nan_positions = {
    "temperature": [3, 11, 19],
    "humidity":    [7, 15],
    "pressure":    [0, 23],
    "wind_speed":  [5, 12, 17, 22],
}

csv_lines = ["hour,temperature_C,humidity_pct,pressure_hPa,wind_speed_kmh"]
for h in hours:
    t = "" if h in nan_positions["temperature"] else str(temperature[h])
    hu = "" if h in nan_positions["humidity"] else str(humidity[h])
    p = "" if h in nan_positions["pressure"] else str(pressure[h])
    w = "" if h in nan_positions["wind_speed"] else str(wind_speed[h])
    csv_lines.append(f"{h},{t},{hu},{p},{w}")

csv_content = "\n".join(csv_lines) + "\n"
csv_path = os.path.join(workspace, "project/data/raw/sensor_readings_day42.csv")
with open(csv_path, "w") as f:
    f.write(csv_content)

# ── Calibration constants file ────────────────────────────────────────────────
# Each sensor has a gain and offset: calibrated = raw * gain + offset
# Stored as a simple .mat-like text spec (agent must embed these in the script)
calib_content = (
    "% Calibration constants for WS-042\n"
    "% Format: sensor, gain, offset\n"
    "temperature,  1.02,  -0.5\n"
    "humidity,     0.98,   1.2\n"
    "pressure,     1.00,   0.0\n"
    "wind_speed,   1.05,  -0.8\n"
)
calib_path = os.path.join(workspace, "project/config/calibration_WS042.txt")
with open(calib_path, "w") as f:
    f.write(calib_content)

# ── Task specification file (business requirements) ───────────────────────────
task_spec = """\
TASK: Daily Sensor Pipeline — Station WS-042
=============================================

Input:  project/data/raw/sensor_readings_day42.csv
Output: project/data/processed/daily_stats.json

Steps:
  1. Load the CSV. Missing values (empty fields) must be treated as NaN.
  2. Apply calibration: calibrated = raw * gain + offset
       temperature : gain=1.02, offset=-0.5
       humidity    : gain=0.98, offset=1.2
       pressure    : gain=1.00, offset=0.0
       wind_speed  : gain=1.05, offset=-0.8
  3. For each channel compute (ignoring NaN values):
       - mean
       - max
       - min
       - nan_count  (number of NaN entries in that channel)
  4. Normalize each channel to [0,1] using its valid (non-NaN) min and max
     after calibration.
  5. Write daily_stats.json with the statistics for each channel.

The pipeline must be implemented as a single Octave/MATLAB script:
    project/scripts/process_sensor_day.m

Running:  octave --no-gui project/scripts/process_sensor_day.m
must produce the JSON output file without errors.
"""
with open(os.path.join(workspace, "TASK.md"), "w") as f:
    f.write(task_spec)

print("Workspace generated successfully.")
print("Key files:")
print(f"  CSV input : project/data/raw/sensor_readings_day42.csv")
print(f"  Calib     : project/config/calibration_WS042.txt")
print(f"  Task spec : TASK.md")