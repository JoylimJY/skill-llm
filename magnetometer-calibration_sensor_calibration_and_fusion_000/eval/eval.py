import sys
import json
import numpy as np
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
passed_all = True

def fail_check(name, detail):
    return {"name": name, "passed": False, "detail": detail}

def pass_check(name, detail):
    return {"name": name, "passed": True, "detail": detail}

# ── Find the output file ───────────────────────────────────────────────────────
try:
    candidates = list(workspace.rglob("calibration_report.json"))
    if not candidates:
        checks.append(fail_check("output_file_exists", "calibration_report.json not found anywhere in workspace."))
        passed_all = False
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        sys.exit(0)
    report_path = candidates[0]
    checks.append(pass_check("output_file_exists", f"Found at {report_path}"))
except Exception as e:
    checks.append(fail_check("output_file_exists", f"Exception: {e}"))
    passed_all = False
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Load JSON ─────────────────────────────────────────────────────────────────
try:
    with open(report_path) as f:
        report = json.load(f)
    checks.append(pass_check("json_valid", "File is valid JSON."))
except Exception as e:
    checks.append(fail_check("json_valid", f"Failed to parse JSON: {e}"))
    passed_all = False
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Check required keys ───────────────────────────────────────────────────────
required_keys = {"Sm", "h", "calibrated_readings"}
missing = required_keys - set(report.keys())
if missing:
    checks.append(fail_check("required_keys", f"Missing keys: {missing}"))
    passed_all = False
else:
    checks.append(pass_check("required_keys", "All required keys present: Sm, h, calibrated_readings"))

# ── Validate Sm (soft-iron matrix) ────────────────────────────────────────────
try:
    Sm = np.array(report["Sm"], dtype=float)
    assert Sm.shape == (3, 3), f"Expected shape (3,3), got {Sm.shape}"
    checks.append(pass_check("Sm_shape", f"Sm has correct shape (3,3)."))
except Exception as e:
    checks.append(fail_check("Sm_shape", f"Sm shape/type error: {e}"))
    passed_all = False
    Sm = None

# ── Validate h (hard-iron offset) ─────────────────────────────────────────────
try:
    h = np.array(report["h"], dtype=float)
    assert h.shape == (3,), f"Expected shape (3,), got {h.shape}"
    checks.append(pass_check("h_shape", f"h has correct shape (3,)."))
except Exception as e:
    checks.append(fail_check("h_shape", f"h shape/type error: {e}"))
    passed_all = False
    h = None

# ── Validate calibrated_readings ─────────────────────────────────────────────
try:
    cal_readings = np.array(report["calibrated_readings"], dtype=float)
    assert cal_readings.shape == (50, 3), f"Expected shape (50,3), got {cal_readings.shape}"
    checks.append(pass_check("calibrated_readings_shape", "calibrated_readings has correct shape (50,3)."))
except Exception as e:
    checks.append(fail_check("calibrated_readings_shape", f"calibrated_readings shape/type error: {e}"))
    passed_all = False
    cal_readings = None

# ── Check calibration quality: Sm should be close to true soft-iron ───────────
# True Sm used to generate data
Sm_true = np.array([
    [1.05, 0.03, -0.01],
    [0.03, 0.98,  0.02],
    [-0.01, 0.02, 1.03]
])
h_true = np.array([8.5, -12.3, 4.7])

if Sm is not None:
    try:
        # The calibrated Sm may be in a different but equivalent form
        # Check that applying calibration reduces the spread of norms
        # Load the raw new readings
        raw_path = workspace / "drone_logs/calibration_session/new_flight_mag_readings.csv"
        raw_data = np.loadtxt(raw_path, delimiter=",", skiprows=1)
        new_raw = raw_data[:, 1:4]  # mx, my, mz columns

        # Compute norms before and after calibration
        norms_raw = np.linalg.norm(new_raw, axis=1)
        std_raw = np.std(norms_raw)

        # Apply agent's calibration formula: Sm @ (m_raw - h)
        cal_check = np.array([Sm @ (new_raw[i] - h) for i in range(len(new_raw))])
        norms_cal = np.linalg.norm(cal_check, axis=1)
        std_cal = np.std(norms_cal)

        # Good calibration should reduce std of norms significantly
        ratio = std_cal / (std_raw + 1e-9)
        if ratio < 0.6:
            checks.append(pass_check("calibration_quality",
                f"Calibration improved norm consistency: std_raw={std_raw:.4f}, std_cal={std_cal:.4f}, ratio={ratio:.3f}"))
        else:
            checks.append(fail_check("calibration_quality",
                f"Calibration did not sufficiently reduce norm spread: std_raw={std_raw:.4f}, std_cal={std_cal:.4f}, ratio={ratio:.3f} (expected <0.6)"))
            passed_all = False
    except Exception as e:
        checks.append(fail_check("calibration_quality", f"Exception during quality check: {e}"))
        passed_all = False

# ── Check calibrated_readings are consistent with Sm and h applied to new_raw ─
if Sm is not None and h is not None and cal_readings is not None:
    try:
        raw_path = workspace / "drone_logs/calibration_session/new_flight_mag_readings.csv"
        raw_data = np.loadtxt(raw_path, delimiter=",", skiprows=1)
        new_raw = raw_data[:, 1:4]

        expected = np.array([Sm @ (new_raw[i] - h) for i in range(len(new_raw))])
        max_diff = np.max(np.abs(cal_readings - expected))

        if max_diff < 1e-3:
            checks.append(pass_check("calibrated_readings_formula",
                f"Calibrated readings correctly apply Sm @ (m_raw - h). Max diff: {max_diff:.6f}"))
        else:
            checks.append(fail_check("calibrated_readings_formula",
                f"Calibrated readings do NOT correctly apply Sm @ (m_raw - h). Max diff: {max_diff:.6f}. "
                "Likely wrong formula order (e.g., Sm @ m_raw - h instead of Sm @ (m_raw - h))."))
            passed_all = False
    except Exception as e:
        checks.append(fail_check("calibrated_readings_formula", f"Exception: {e}"))
        passed_all = False

# ── Compute final score ───────────────────────────────────────────────────────
n_passed = sum(1 for c in checks if c["passed"])
score = round(n_passed / len(checks), 3)
passed_all = passed_all and all(c["passed"] for c in checks)

print(json.dumps({
    "passed": passed_all,
    "score": score,
    "checks": checks
}, indent=2))