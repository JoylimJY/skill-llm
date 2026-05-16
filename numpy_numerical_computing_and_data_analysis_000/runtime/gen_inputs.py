import os
import random
import csv
import json

random.seed(42)

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "plant_data/line_A/raw",
    "plant_data/line_A/processed",
    "plant_data/line_B/raw",
    "plant_data/line_B/processed",
    "plant_data/metadata",
    "plant_data/reports/daily",
    "plant_data/reports/weekly",
    "plant_data/calibration",
    "plant_data/archive/2023",
    "plant_data/archive/2024",
    "logs",
    "config",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "plant_data/metadata/sensor_registry.json": json.dumps({
        "line_A": {"count": 8, "unit": "bar", "sampling_hz": 10},
        "line_B": {"count": 6, "unit": "bar", "sampling_hz": 10},
        "notes": "Sensors replaced 2024-03-01"
    }, indent=2),
    "plant_data/calibration/offsets.csv": "sensor_id,offset\nA1,0.02\nA2,-0.01\nA3,0.00\nB1,0.03\nB2,-0.02",
    "plant_data/reports/daily/2024-05-01.txt": "All sensors nominal. No anomalies detected.",
    "plant_data/reports/weekly/week18.txt": "Maintenance window completed. Sensors recalibrated.",
    "plant_data/archive/2023/backup_summary.json": json.dumps({"archived": 1200, "flagged": 4}),
    "plant_data/archive/2024/backup_summary.json": json.dumps({"archived": 980, "flagged": 1}),
    "logs/pipeline.log": "2024-05-01 08:00:00 INFO  Pipeline started\n2024-05-01 08:01:00 INFO  Data loaded\n",
    "config/thresholds.json": json.dumps({"pressure_max": 12.5, "temp_max": 95.0}),
    "plant_data/line_A/processed/summary_stats.txt": "mean=6.34 std=1.12 min=3.20 max=9.87",
    "plant_data/line_B/processed/summary_stats.txt": "mean=5.98 std=0.89 min=4.01 max=8.44",
    "plant_data/metadata/pipeline_version.txt": "v2.3.1-release",
}
for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# ── CORE PROBLEM DATA ───────────────────────────────────────────────────────
# sensor_group_A.csv : 8 sensors × 120 time-steps of pressure readings
# sensor_group_B.csv : 6 sensors × 120 time-steps of pressure readings
# Each row = one sensor; each column = one time-step

import numpy as np
rng = np.random.default_rng(42)

N_STEPS = 120

# Group A: 8 sensors
group_a = rng.normal(loc=6.0, scale=1.5, size=(8, N_STEPS)).round(4)
# Inject realistic sensor drift / anomalies
group_a[2, 40:60] += 3.5   # sensor 3 spike
group_a[5, :] *= 0.6        # sensor 6 suppressed

# Group B: 6 sensors
group_b = rng.normal(loc=5.8, scale=1.2, size=(6, N_STEPS)).round(4)
group_b[1, 70:90] -= 2.8   # sensor 2 dip
group_b[4, :] += 1.1        # sensor 5 elevated

def write_sensor_csv(path, data, label):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        header = ["sensor_id"] + [f"t{i}" for i in range(data.shape[1])]
        writer.writerow(header)
        for i, row in enumerate(data):
            writer.writerow([f"{label}{i+1}"] + list(row))

write_sensor_csv("plant_data/line_A/raw/sensor_group_A.csv", group_a, "A")
write_sensor_csv("plant_data/line_B/raw/sensor_group_B.csv", group_b, "B")

# ── task spec (business brief only) ─────────────────────────────────────────
task_brief = """\
MANUFACTURING ANALYTICS BRIEF
==============================
Plant: SmartFab Line 1 & 2
Task: Sensor Similarity & Dominant-Mode Analysis

Data files:
  - plant_data/line_A/raw/sensor_group_A.csv   (8 sensors, 120 time-steps)
  - plant_data/line_B/raw/sensor_group_B.csv   (6 sensors, 120 time-steps)

See task_spec.md for what needs to be produced.
"""
with open("BRIEF.txt", "w") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print("Files created:")
for d in dirs:
    print(f"  {d}/")
for p in distractors:
    print(f"  {p}")
print("  plant_data/line_A/raw/sensor_group_A.csv")
print("  plant_data/line_B/raw/sensor_group_B.csv")