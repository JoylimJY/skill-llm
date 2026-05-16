#!/usr/bin/env python3
"""
Evaluation script for the mac-health-check skill task.

Checks:
1. health_report.json exists somewhere in the workspace
2. It is valid JSON
3. It was derived from the LAST non-empty JSON line (not an earlier sample)
   - cpu_temp_c must be ~88.4 (last sample), not 51.2 or 62.7
4. CPU and GPU usage fractions were correctly converted to percentages
   - pcpu_pct must be ~93.0 (0.93 * 100), not 0.93
   - ecpu_pct must be ~87.0
   - gpu_pct must be ~72.0
5. Swap usage is correctly reported as > 0
6. Interpretation field is present and mentions thermal pressure / hot temp
7. RAM fields are in GB (not raw bytes)
"""

import json
import sys
from pathlib import Path


def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    score = 0.0

    # ── Check 1: Find health_report.json
    candidates = list(ws.rglob("health_report.json"))
    if not candidates:
        checks.append({
            "name": "health_report.json exists",
            "passed": False,
            "detail": "No health_report.json found anywhere in the workspace."
        })
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = candidates[0]
    checks.append({
        "name": "health_report.json exists",
        "passed": True,
        "detail": f"Found at {report_path}"
    })
    score += 0.1

    # ── Check 2: Valid JSON
    try:
        with open(report_path) as f:
            report = json.load(f)
        checks.append({
            "name": "health_report.json is valid JSON",
            "passed": True,
            "detail": "Parsed successfully."
        })
        score += 0.1
    except Exception as e:
        checks.append({
            "name": "health_report.json is valid JSON",
            "passed": False,
            "detail": f"JSON parse error: {e}"
        })
        print(json.dumps({"passed": False, "score": score, "checks": checks}))
        return

    # ── Check 3: Derived from LAST non-empty line (cpu_temp must be ~88.4)
    try:
        cpu_temp = float(report.get("cpu_temp_c", -999))
        correct_last_temp = abs(cpu_temp - 88.4) < 1.0
        wrong_first = abs(cpu_temp - 51.2) < 2.0
        wrong_second = abs(cpu_temp - 62.7) < 2.0
        if correct_last_temp:
            detail = f"cpu_temp_c={cpu_temp} matches last sample (~88.4C). Correct."
        elif wrong_first or wrong_second:
            detail = f"cpu_temp_c={cpu_temp} matches an earlier sample, not the last. Agent failed the last-line rule."
        else:
            detail = f"cpu_temp_c={cpu_temp} does not match any known sample. Unexpected value."
        checks.append({
            "name": "Used last non-empty JSONL line as sample (cpu_temp ~88.4C)",
            "passed": correct_last_temp,
            "detail": detail
        })
        if correct_last_temp:
            score += 0.2
    except Exception as e:
        checks.append({
            "name": "Used last non-empty JSONL line as sample (cpu_temp ~88.4C)",
            "passed": False,
            "detail": f"Could not read cpu_temp_c: {e}"
        })

    # ── Check 4a: P-CPU fraction → percentage (~93.0)
    try:
        pcpu_pct = float(report.get("pcpu_pct", -999))
        # Accept if in percent range: 90..96
        pct_correct = 90.0 <= pcpu_pct <= 96.0
        raw_fraction = abs(pcpu_pct - 0.93) < 0.05  # agent left it as fraction
        if pct_correct:
            detail = f"pcpu_pct={pcpu_pct}% correctly converted from fraction."
        elif raw_fraction:
            detail = f"pcpu_pct={pcpu_pct} looks like the raw fraction (0.93), not a percentage."
        else:
            detail = f"pcpu_pct={pcpu_pct} is unexpected (expected ~93.0)."
        checks.append({
            "name": "P-CPU fraction converted to percentage (~93%)",
            "passed": pct_correct,
            "detail": detail
        })
        if pct_correct:
            score += 0.1
    except Exception as e:
        checks.append({
            "name": "P-CPU fraction converted to percentage (~93%)",
            "passed": False,
            "detail": f"Could not read pcpu_pct: {e}"
        })

    # ── Check 4b: GPU fraction → percentage (~72.0)
    try:
        gpu_pct = float(report.get("gpu_pct", -999))
        pct_correct = 68.0 <= gpu_pct <= 76.0
        raw_fraction = abs(gpu_pct - 0.72) < 0.05
        if pct_correct:
            detail = f"gpu_pct={gpu_pct}% correctly converted from fraction."
        elif raw_fraction:
            detail = f"gpu_pct={gpu_pct} looks like the raw fraction (0.72), not a percentage."
        else:
            detail = f"gpu_pct={gpu_pct} is unexpected (expected ~72.0)."
        checks.append({
            "name": "GPU fraction converted to percentage (~72%)",
            "passed": pct_correct,
            "detail": detail
        })
        if pct_correct:
            score += 0.1
    except Exception as e:
        checks.append({
            "name": "GPU fraction converted to percentage (~72%)",
            "passed": False,
            "detail": f"Could not read gpu_pct: {e}"
        })

    # ── Check 5: Swap usage > 0 (last sample has swap_usage = 1073741824 bytes = 1 GB)
    try:
        swap_usage_gb = float(report.get("swap_usage_gb", -1))
        swap_positive = swap_usage_gb > 0.0
        swap_reasonable = 0.9 <= swap_usage_gb <= 1.1  # ~1 GB
        if swap_reasonable:
            detail = f"swap_usage_gb={swap_usage_gb} correctly shows ~1 GB in use."
        elif swap_positive:
            detail = f"swap_usage_gb={swap_usage_gb} is positive but unexpected magnitude (expected ~1.0 GB)."
        else:
            detail = f"swap_usage_gb={swap_usage_gb} is zero or negative; expected >0 from last sample."
        checks.append({
            "name": "Swap usage correctly reported as ~1 GB (not 0)",
            "passed": swap_reasonable,
            "detail": detail
        })
        if swap_reasonable:
            score += 0.15
    except Exception as e:
        checks.append({
            "name": "Swap usage correctly reported as ~1 GB (not 0)",
            "passed": False,
            "detail": f"Could not read swap_usage_gb: {e}"
        })

    # ── Check 6: Interpretation field present and mentions hot/thermal/pressure
    try:
        interp = str(report.get("interpretation", "")).lower()
        has_interp = bool(interp.strip())
        thermal_keywords = ["hot", "thermal", "85", "pressure", "sustained", "85c"]
        mentions_thermal = any(kw in interp for kw in thermal_keywords)
        if not has_interp:
            detail = "interpretation field is missing or empty."
        elif mentions_thermal:
            detail = f"interpretation mentions thermal concern. Content: '{interp[:120]}'"
        else:
            detail = f"interpretation present but doesn't mention thermal concern. Content: '{interp[:120]}'"
        checks.append({
            "name": "Interpretation mentions high temperature / thermal pressure",
            "passed": has_interp and mentions_thermal,
            "detail": detail
        })
        if has_interp and mentions_thermal:
            score += 0.1
    except Exception as e:
        checks.append({
            "name": "Interpretation mentions high temperature / thermal pressure",
            "passed": False,
            "detail": f"Error reading interpretation: {e}"
        })

    # ── Check 7: RAM fields in GB (not raw bytes)
    try:
        ram_total_gb = float(report.get("ram_total_gb", -1))
        # 17179869184 bytes = ~16 GB
        ram_correct = 15.0 <= ram_total_gb <= 17.0
        is_raw_bytes = ram_total_gb > 1e9
        if ram_correct:
            detail = f"ram_total_gb={ram_total_gb} correctly expressed in GB (~16 GB)."
        elif is_raw_bytes:
            detail = f"ram_total_gb={ram_total_gb} looks like raw bytes, not GB."
        else:
            detail = f"ram_total_gb={ram_total_gb} is unexpected (expected ~16.0 GB)."
        checks.append({
            "name": "RAM total expressed in GB (~16 GB), not raw bytes",
            "passed": ram_correct,
            "detail": detail
        })
        if ram_correct:
            score += 0.1
    except Exception as e:
        checks.append({
            "name": "RAM total expressed in GB (~16 GB), not raw bytes",
            "passed": False,
            "detail": f"Could not read ram_total_gb: {e}"
        })

    # ── Check 8: sys_power correctly captured (~52.6 W from last sample)
    try:
        sys_power = float(report.get("sys_power_w", -1))
        power_correct = 51.0 <= sys_power <= 54.0
        if power_correct:
            detail = f"sys_power_w={sys_power} correctly matches last sample (~52.6 W)."
        else:
            detail = f"sys_power_w={sys_power} doesn't match last sample (~52.6 W)."
        checks.append({
            "name": "sys_power_w matches last sample (~52.6 W)",
            "passed": power_correct,
            "detail": detail
        })
        if power_correct:
            score += 0.05
    except Exception as e:
        checks.append({
            "name": "sys_power_w matches last sample (~52.6 W)",
            "passed": False,
            "detail": f"Could not read sys_power_w: {e}"
        })

    # Final pass/fail: all critical checks must pass
    critical_checks = [
        "health_report.json exists",
        "health_report.json is valid JSON",
        "Used last non-empty JSONL line as sample (cpu_temp ~88.4C)",
        "P-CPU fraction converted to percentage (~93%)",
        "Swap usage correctly reported as ~1 GB (not 0)",
    ]
    critical_results = {c["name"]: c["passed"] for c in checks}
    all_critical_passed = all(critical_results.get(name, False) for name in critical_checks)

    score = round(min(score, 1.0), 3)

    print(json.dumps({
        "passed": all_critical_passed,
        "score": score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "arg", "passed": False, "detail": "No workspace path given"}]}))
        sys.exit(1)
    run_eval(sys.argv[1])