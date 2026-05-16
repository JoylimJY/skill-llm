#!/usr/bin/env python3
import sys
import json
import subprocess
import math
import os
from pathlib import Path

workspace = sys.argv[1]
checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ── 1. Script file exists ────────────────────────────────────────────────────
script_path = Path(workspace) / "project/scripts/process_sensor_day.m"
if not script_path.exists():
    checks.append(make_check("script_exists", False, "process_sensor_day.m not found"))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
checks.append(make_check("script_exists", True, str(script_path)))

# ── 2. Script runs without error ─────────────────────────────────────────────
try:
    result = subprocess.run(
        ["octave", "--no-gui", str(script_path)],
        capture_output=True, text=True, timeout=60,
        cwd=workspace
    )
    if result.returncode != 0:
        detail = f"Exit code {result.returncode}. stderr: {result.stderr[:500]}"
        checks.append(make_check("script_runs", False, detail))
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        sys.exit(0)
    checks.append(make_check("script_runs", True, "Octave exited 0"))
except subprocess.TimeoutExpired:
    checks.append(make_check("script_runs", False, "Timed out after 60s"))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
except Exception as e:
    checks.append(make_check("script_runs", False, str(e)))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 3. Output JSON exists ────────────────────────────────────────────────────
output_path = Path(workspace) / "project/data/processed/daily_stats.json"
if not output_path.exists():
    checks.append(make_check("output_exists", False, "daily_stats.json not found"))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
checks.append(make_check("output_exists", True, str(output_path)))

# ── 4. Parse JSON ────────────────────────────────────────────────────────────
try:
    with open(output_path) as f:
        stats = json.load(f)
    checks.append(make_check("json_valid", True, "Parsed OK"))
except Exception as e:
    checks.append(make_check("json_valid", False, f"JSON parse error: {e}"))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Reference computation ─────────────────────────────────────────────────────
import math

raw_data = {
    "temperature_C":  [-5.49,-4.64,-2.78,None,-0.28,0.56,2.14,3.36,3.68,4.22,3.35,None,1.40,0.24,-1.19,-2.64,-4.08,-4.88,-5.49,None,-4.28,-2.78,-0.28,1.40],
    "humidity_pct":   [79.35,73.18,66.08,59.94,55.91,53.89,54.08,None,58.29,62.25,66.31,70.81,75.08,78.35,None,80.93,79.35,76.08,73.18,70.81,67.08,63.94,59.94,56.08],
    "pressure_hPa":   [None,1011.64,1011.22,1012.03,1013.08,1014.17,1015.02,1015.31,1014.88,1013.75,1012.36,1011.08,1010.09,1009.83,1010.29,1011.44,1013.08,1014.88,1015.98,1016.08,1014.88,1012.36,1009.83,None],
    "wind_speed_kmh": [24.38,22.14,18.53,14.09,9.84,None,4.78,4.09,7.12,12.43,18.47,23.56,None,28.43,26.09,20.47,14.09,None,9.84,6.09,3.78,3.09,None,7.12],
}

# Re-parse the actual CSV to get ground-truth raws
csv_path = Path(workspace) / "project/data/raw/sensor_readings_day42.csv"
raw_parsed = {"temperature_C": [], "humidity_pct": [], "pressure_hPa": [], "wind_speed_kmh": []}
try:
    with open(csv_path) as f:
        lines = f.read().strip().splitlines()
    header = lines[0].split(",")
    col_map = {h.strip(): i for i, h in enumerate(header)}
    channels = ["temperature_C", "humidity_pct", "pressure_hPa", "wind_speed_kmh"]
    for line in lines[1:]:
        parts = line.split(",")
        for ch in channels:
            val = parts[col_map[ch]].strip() if col_map[ch] < len(parts) else ""
            raw_parsed[ch].append(float(val) if val != "" else None)
except Exception as e:
    checks.append(make_check("reference_compute", False, f"Could not parse CSV: {e}"))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

calib = {
    "temperature_C":  (1.02, -0.5),
    "humidity_pct":   (0.98,  1.2),
    "pressure_hPa":   (1.00,  0.0),
    "wind_speed_kmh": (1.05, -0.8),
}

ref = {}
for ch, values in raw_parsed.items():
    gain, offset = calib[ch]
    calib_vals = [v * gain + offset if v is not None else None for v in values]
    valid = [v for v in calib_vals if v is not None]
    nan_count = sum(1 for v in calib_vals if v is None)
    ch_min = min(valid)
    ch_max = max(valid)
    ref[ch] = {
        "mean":      sum(valid) / len(valid),
        "max":       ch_max,
        "min":       ch_min,
        "nan_count": nan_count,
        "_calib_vals": calib_vals,
        "_valid_min":  ch_min,
        "_valid_max":  ch_max,
    }

# ── 5. Check per-channel statistics ──────────────────────────────────────────
channel_keys = {
    "temperature_C":  ["temperature", "temperature_C", "temp"],
    "humidity_pct":   ["humidity", "humidity_pct"],
    "pressure_hPa":   ["pressure", "pressure_hPa"],
    "wind_speed_kmh": ["wind_speed", "wind_speed_kmh"],
}

TOL = 0.05  # 5% relative tolerance or absolute 0.01

def find_channel(stats_dict, candidates):
    for c in candidates:
        if c in stats_dict:
            return stats_dict[c]
    return None

all_stats_ok = True
for ch, aliases in channel_keys.items():
    ch_stats = find_channel(stats, aliases)
    if ch_stats is None:
        checks.append(make_check(f"channel_{ch}_present", False, f"No key found for {ch}"))
        all_stats_ok = False
        continue
    checks.append(make_check(f"channel_{ch}_present", True, "Found"))

    r = ref[ch]
    for stat_name in ["mean", "max", "min", "nan_count"]:
        expected = r[stat_name]
        try:
            got = float(ch_stats[stat_name])
        except (KeyError, TypeError, ValueError) as e:
            checks.append(make_check(f"{ch}_{stat_name}", False, f"Missing or invalid: {e}"))
            all_stats_ok = False
            continue

        if stat_name == "nan_count":
            ok = (int(got) == int(expected))
            checks.append(make_check(f"{ch}_{stat_name}", ok,
                f"expected={int(expected)}, got={int(got)}"))
            if not ok:
                all_stats_ok = False
        else:
            if abs(expected) > 1e-9:
                rel_err = abs(got - expected) / abs(expected)
                ok = rel_err < TOL
            else:
                ok = abs(got - expected) < 0.01
            checks.append(make_check(f"{ch}_{stat_name}", ok,
                f"expected={expected:.4f}, got={got:.4f}"))
            if not ok:
                all_stats_ok = False

# ── 6. Check script for element-wise operator usage (no silent matrix bug) ───
try:
    script_src = script_path.read_text()

    # Must use .* or ./ or .^ for element-wise calibration (gain * raw)
    has_elementwise = (".*" in script_src or "./" in script_src or ".^" in script_src)
    checks.append(make_check("uses_elementwise_ops", has_elementwise,
        "Script must use .* ./ .^ for element-wise operations"))

    # Must NOT use bare == NaN or ~= NaN for NaN detection (must use isnan)
    import re
    bad_nan_check = bool(re.search(r'[=~]=\s*[Nn]a[Nn]', script_src))
    checks.append(make_check("no_bare_nan_comparison", not bad_nan_check,
        "'== NaN' or '~= NaN' detected; must use isnan()"))

    # Must use isnan somewhere
    has_isnan = "isnan" in script_src
    checks.append(make_check("uses_isnan", has_isnan,
        "Must use isnan() for NaN detection"))

    # Must NOT use i or j as loop variable names (imaginary unit trap)
    bad_loop_vars = bool(re.search(r'\bfor\s+(i|j)\s*=', script_src))
    checks.append(make_check("no_ij_loop_vars", not bad_loop_vars,
        "Using i or j as loop variable shadows imaginary unit in MATLAB/Octave"))

    if bad_loop_vars or bad_nan_check or not has_isnan or not has_elementwise:
        all_stats_ok = False

except Exception as e:
    checks.append(make_check("script_source_check", False, str(e)))
    all_stats_ok = False

# ── 7. omitnan or equivalent NaN-ignoring logic ──────────────────────────────
try:
    omitnan_or_manual = ("omitnan" in script_src) or ("isnan" in script_src)
    checks.append(make_check("nan_aware_stats", omitnan_or_manual,
        "Must handle NaN in statistics (omitnan flag or manual isnan filtering)"))
    if not omitnan_or_manual:
        all_stats_ok = False
except Exception as e:
    checks.append(make_check("nan_aware_stats", False, str(e)))
    all_stats_ok = False

# ── Final score ───────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / total if total > 0 else 0.0
final_passed = all(c["passed"] for c in checks)

print(json.dumps({
    "passed": final_passed,
    "score": round(score, 3),
    "checks": checks
}, indent=2))