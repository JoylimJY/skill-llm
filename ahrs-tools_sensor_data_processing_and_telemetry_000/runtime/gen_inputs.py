import os
import random
import numpy as np
import json

random.seed(42)
np.random.seed(42)

WORKSPACE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "telemetry/raw/flight_001",
    "telemetry/raw/flight_002",
    "telemetry/processed",
    "telemetry/archive",
    "config/sensors",
    "config/calibration",
    "logs/system",
    "logs/errors",
    "docs/hardware",
    "scripts/legacy",
    "scripts/utils",
    "reports/weekly",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "config/sensors/imu_config.yaml": """\
sensor_id: IMU-9250
sample_rate_hz: 200
axes_convention: NED
filter_type: mahony
""",
    "config/calibration/accel_offsets.json": json.dumps({"x": 0.012, "y": -0.003, "z": 9.801}),
    "config/calibration/gyro_bias.csv": "axis,bias_dps\nx,0.02\ny,-0.01\nz,0.005\n",
    "logs/system/boot.log": "2024-01-10 08:00:00 [INFO] IMU initialized\n2024-01-10 08:00:01 [INFO] AHRS filter started\n",
    "logs/errors/dropped_packets.log": "2024-01-10 08:05:12 [WARN] packet #445 dropped\n2024-01-10 08:07:33 [WARN] packet #891 dropped\n",
    "docs/hardware/drone_spec.md": "# Drone Spec\nModel: HexaCopter-X\nIMU: MPU-9250\nFirmware: v3.2.1\n",
    "scripts/legacy/old_ekf.py": "# deprecated EKF implementation\nimport numpy as np\n# ...\n",
    "scripts/utils/serial_reader.py": "# utility to read serial IMU output\nimport serial\n",
    "reports/weekly/week01_summary.txt": "Week 01: 12 flights, avg duration 8.3 min, no anomalies.\n",
    "telemetry/archive/flight_000_backup.csv": "# old format - do not use\nts,q0,q1,q2,q3\n0,1,0,0,0\n",
    "telemetry/processed/.gitkeep": "",
    "scripts/legacy/euler_convert.py": "# naive euler conversion - superseded\nimport math\ndef q_to_euler(q): pass\n",
}
for path, content in distractors.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# ── generate the messy sensor log ───────────────────────────────────────────
# Format: timestamp_ms, w, x, y, z  (but with comments, blank lines, and some
# rows where the order is labeled as x,y,z,w to trap naïve agents — however
# the *actual* data is always w,x,y,z as per pywayne convention)
# We will include header confusion comments.

def random_unit_quat(rng):
    """Generate a random unit quaternion."""
    v = rng.standard_normal(4)
    v /= np.linalg.norm(v)
    return v  # w, x, y, z

rng = np.random.default_rng(42)

# 20 valid quaternion records
records = []
for i in range(20):
    ts = 1000 + i * 50
    q = random_unit_quat(rng)
    records.append((ts, q))

# Build the messy CSV
messy_lines = [
    "# UAV AHRS Telemetry Dump — Flight 001",
    "# Sensor: MPU-9250 | Filter: Mahony | Rate: 20Hz",
    "# WARNING: legacy columns below are x,y,z,w but actual data order is w,x,y,z",
    "# Do NOT reorder columns — firmware quirk retained for compatibility",
    "# timestamp_ms, qw, qx, qy, qz",
    "",
]

for i, (ts, q) in enumerate(records):
    w, x, y, z = q
    # Sprinkle in blank lines and comment lines
    if i == 5:
        messy_lines.append("# mid-flight recalibration event at t=1250ms")
        messy_lines.append("")
    if i == 12:
        messy_lines.append("")
        messy_lines.append("# brief GPS outage — IMU-only mode")
    # One row with extra trailing whitespace, one with extra spaces between commas
    if i == 3:
        messy_lines.append(f"  {ts} , {w:.8f} , {x:.8f} , {y:.8f} , {z:.8f}  ")
    elif i == 9:
        messy_lines.append(f"{ts},{w:.8f},{x:.8f},{y:.8f},{z:.8f}   ")
    else:
        messy_lines.append(f"{ts},{w:.8f},{x:.8f},{y:.8f},{z:.8f}")

sensor_log_path = os.path.join(WORKSPACE, "telemetry/raw/flight_001/imu_log.csv")
with open(sensor_log_path, "w") as f:
    f.write("\n".join(messy_lines) + "\n")

# ── store ground truth for eval ──────────────────────────────────────────────
# We store the raw records so the eval script can recompute independently
gt = []
for ts, q in records:
    gt.append({
        "timestamp_ms": int(ts),
        "w": float(q[0]),
        "x": float(q[1]),
        "y": float(q[2]),
        "z": float(q[3]),
    })

gt_path = os.path.join(WORKSPACE, "telemetry/raw/flight_001/_ground_truth_DO_NOT_EDIT.json")
with open(gt_path, "w") as f:
    json.dump(gt, f, indent=2)

print("Workspace generated successfully.")
print(f"Sensor log: {sensor_log_path}")
print(f"Ground truth: {gt_path}")