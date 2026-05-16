import numpy as np
import os
import json
import csv

# Fixed seed for determinism
rng = np.random.default_rng(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure with distractors ──────────────────────────────────────
dirs = [
    "drone_logs/flight_001",
    "drone_logs/flight_002",
    "drone_logs/calibration_session",
    "drone_logs/archive",
    "config",
    "scripts",
    "reports/raw",
    "reports/processed",
    "hardware/imu_specs",
    "hardware/firmware",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractor_content = {
    "config/drone_config.json": json.dumps({"model": "Falcon-7", "imu": "ICM-42688-P", "sample_rate_hz": 100}),
    "config/flight_params.yaml": "max_altitude: 120\nmax_speed_mps: 15\nfailsafe_return: true\n",
    "hardware/imu_specs/ICM42688P_datasheet.txt": "ICM-42688-P IMU\nAccelerometer range: ±16g\nGyroscope range: ±2000dps\nMagnetometer: AK09918\n",
    "hardware/firmware/fw_v2.3.1_changelog.txt": "v2.3.1: Fixed gyro bias drift issue at cold start.\nv2.3.0: Initial magnetometer driver support.\n",
    "drone_logs/archive/old_calibration_2023.json": json.dumps({"Sm": [[1,0,0],[0,1,0],[0,0,1]], "h": [0,0,0], "note": "factory defaults"}),
    "scripts/plot_imu.py": "# Placeholder script for plotting IMU data\nimport sys\nprint('Usage: python plot_imu.py <log_file>')\n",
    "scripts/sync_logs.sh": "#!/bin/bash\nrsync -av drone_logs/ backup_server:/drone_backup/\n",
    "reports/raw/flight_001_summary.txt": "Flight 001: Duration 12m34s, Max alt 87m, GPS drift: 0.3m\n",
    "reports/raw/flight_002_summary.txt": "Flight 002: Duration 8m12s, Max alt 54m, GPS drift: 1.1m\n",
    "drone_logs/flight_001/gps_track.csv": "time,lat,lon,alt\n0.0,47.6062,122.3321,10.0\n1.0,47.6063,122.3322,10.5\n",
    "drone_logs/flight_002/gps_track.csv": "time,lat,lon,alt\n0.0,47.6100,122.3400,12.0\n1.0,47.6101,122.3401,12.3\n",
}
for path, content in distractor_content.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ── Generate realistic IMU calibration session data ───────────────────────────
# Simulate a figure-8 / tumbling motion to cover many orientations
# N samples at 100 Hz over 30 seconds
N = 3000
dt = 1.0 / 100.0
ts = np.arange(N) * dt  # shape (N,)

# Simulate orientation via Euler angles sweeping multiple axes
t = ts
phi   = 2 * np.pi * 0.3 * t          # roll
theta = 2 * np.pi * 0.2 * t + 0.5    # pitch
psi   = 2 * np.pi * 0.1 * t          # yaw

# Gravity in body frame (simplified, ~9.81 m/s²)
g = 9.81
acc = np.column_stack([
    -g * np.sin(theta),
     g * np.sin(phi) * np.cos(theta),
     g * np.cos(phi) * np.cos(theta),
]) + rng.normal(0, 0.02, (N, 3))

# Gyroscope: derivatives of Euler angles (rad/s)
dphi   = 2 * np.pi * 0.3 * np.ones(N)
dtheta = 2 * np.pi * 0.2 * np.ones(N)
dpsi   = 2 * np.pi * 0.1 * np.ones(N)
gyro = np.column_stack([dphi, dtheta, dpsi]) + rng.normal(0, 0.005, (N, 3))

# Earth magnetic field reference (uT), mild soft/hard iron distortion
B_earth = np.array([20.0, 5.0, 42.0])  # NED-ish

# True soft-iron matrix (slight distortion)
Sm_true = np.array([
    [1.05, 0.03, -0.01],
    [0.03, 0.98,  0.02],
    [-0.01, 0.02, 1.03]
])
# True hard-iron offset (uT)
h_true = np.array([8.5, -12.3, 4.7])

# Rotation matrix from Euler angles
def rot_matrix(ph, th, ps):
    Rx = np.array([[1,0,0],[0,np.cos(ph),-np.sin(ph)],[0,np.sin(ph),np.cos(ph)]])
    Ry = np.array([[np.cos(th),0,np.sin(th)],[0,1,0],[-np.sin(th),0,np.cos(th)]])
    Rz = np.array([[np.cos(ps),-np.sin(ps),0],[np.sin(ps),np.cos(ps),0],[0,0,1]])
    return Rz @ Ry @ Rx

# Raw magnetometer = rotate earth field into body frame, apply distortion
mag_raw = np.zeros((N, 3))
for i in range(N):
    R = rot_matrix(phi[i], theta[i], psi[i])
    b_body = R.T @ B_earth
    # Inverse of calibration formula to generate "raw" readings
    # raw = Sm_inv @ b_body + h
    Sm_inv = np.linalg.inv(Sm_true)
    mag_raw[i] = Sm_inv @ b_body + h_true + rng.normal(0, 0.3, 3)

# ── Save calibration session data as separate CSV files (messy format) ─────────
# Timestamps: saved as milliseconds integers (agent must convert to seconds)
ts_ms = (ts * 1000).astype(int)

cal_dir = os.path.join(workspace, "drone_logs/calibration_session")

# Save timestamps
np.savetxt(os.path.join(cal_dir, "timestamps_ms.csv"), ts_ms.reshape(-1,1),
           delimiter=",", fmt="%d", header="timestamp_ms", comments="")

# Save accelerometer with a header row and extra metadata column (messy)
with open(os.path.join(cal_dir, "accelerometer.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["sample_id", "ax_mps2", "ay_mps2", "az_mps2", "temp_C"])
    for i in range(N):
        writer.writerow([i, round(acc[i,0],6), round(acc[i,1],6), round(acc[i,2],6), round(25.0 + rng.normal(0,0.1), 2)])

# Save gyroscope with slightly different column naming
with open(os.path.join(cal_dir, "gyroscope.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["sample_id", "roll_rate_rads", "pitch_rate_rads", "yaw_rate_rads"])
    for i in range(N):
        writer.writerow([i, round(gyro[i,0],6), round(gyro[i,1],6), round(gyro[i,2],6)])

# Save magnetometer
with open(os.path.join(cal_dir, "magnetometer.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["sample_id", "mx_uT", "my_uT", "mz_uT"])
    for i in range(N):
        writer.writerow([i, round(mag_raw[i,0],6), round(mag_raw[i,1],6), round(mag_raw[i,2],6)])

# ── Generate a separate set of "new raw readings" to apply calibration to ─────
# These are 50 raw magnetometer readings from a subsequent flight
M = 50
phi_new   = rng.uniform(0, 2*np.pi, M)
theta_new = rng.uniform(-np.pi/2, np.pi/2, M)
psi_new   = rng.uniform(0, 2*np.pi, M)

new_raw = np.zeros((M, 3))
for i in range(M):
    R = rot_matrix(phi_new[i], theta_new[i], psi_new[i])
    b_body = R.T @ B_earth
    Sm_inv = np.linalg.inv(Sm_true)
    new_raw[i] = Sm_inv @ b_body + h_true + rng.normal(0, 0.3, 3)

with open(os.path.join(cal_dir, "new_flight_mag_readings.csv"), "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["reading_id", "mx_uT", "my_uT", "mz_uT"])
    for i in range(M):
        writer.writerow([i, round(new_raw[i,0],6), round(new_raw[i,1],6), round(new_raw[i,2],6)])

print("Workspace generated successfully.")
print(f"Calibration session data: {cal_dir}")
print(f"Samples: {N}, New readings: {M}")