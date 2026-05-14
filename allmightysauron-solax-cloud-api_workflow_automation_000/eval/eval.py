#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    total_score = 0.0

    # ── Check 1: npm dependencies were installed (node_modules exists) ────────
    node_modules = Path(workspace) / "skills" / "solax-summary-fetch" / "scripts" / "node_modules"
    nm_exists = node_modules.exists() and node_modules.is_dir()
    checks.append({
        "name": "npm_install_ran",
        "passed": nm_exists,
        "detail": f"node_modules at {node_modules}: {'found' if nm_exists else 'NOT FOUND. Agent must run npm install (not npm ci).'}"
    })
    if nm_exists:
        total_score += 0.15

    # ── Check 2: output file inverter_summary.json exists somewhere ───────────
    candidates = list(Path(workspace).rglob("inverter_summary.json"))
    file_exists = len(candidates) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"inverter_summary.json found at: {[str(c) for c in candidates]}" if file_exists else "inverter_summary.json not found anywhere in workspace."
    })
    if not file_exists:
        checks.append({"name": "output_json_valid", "passed": False, "detail": "Skipped — file not found."})
        checks.append({"name": "summary_ok_true", "passed": False, "detail": "Skipped — file not found."})
        checks.append({"name": "summary_required_fields", "passed": False, "detail": "Skipped — file not found."})
        checks.append({"name": "summary_values_correct", "passed": False, "detail": "Skipped — file not found."})
        return checks, total_score

    total_score += 0.15
    output_file = candidates[0]

    # ── Check 3: file contains valid JSON ─────────────────────────────────────
    try:
        with open(output_file) as f:
            data = json.load(f)
        valid_json = True
        json_detail = "Valid JSON parsed successfully."
    except Exception as e:
        valid_json = False
        data = {}
        json_detail = f"JSON parse error: {e}"

    checks.append({"name": "output_json_valid", "passed": valid_json, "detail": json_detail})
    if not valid_json:
        checks.append({"name": "summary_ok_true", "passed": False, "detail": "Skipped — invalid JSON."})
        checks.append({"name": "summary_required_fields", "passed": False, "detail": "Skipped — invalid JSON."})
        checks.append({"name": "summary_values_correct", "passed": False, "detail": "Skipped — invalid JSON."})
        return checks, total_score

    total_score += 0.10

    # ── Check 4: ok == true (not an error response) ───────────────────────────
    ok_true = data.get("ok") is True
    checks.append({
        "name": "summary_ok_true",
        "passed": ok_true,
        "detail": f"ok={data.get('ok')}. Expected True. Error field: {data.get('error', 'N/A')}"
    })
    if ok_true:
        total_score += 0.20

    # ── Check 5: all SolaxSummary required fields present ─────────────────────
    required_fields = [
        "ok", "sn", "inverterType", "powerdc1", "powerdc2", "acpower",
        "yieldtoday", "yieldtotal", "feedinpower", "feedinenergy",
        "consumeenergy", "soc", "peps1", "peps2", "peps3", "batPower", "uploadTime"
    ]
    missing = [f for f in required_fields if f not in data]
    fields_ok = len(missing) == 0
    checks.append({
        "name": "summary_required_fields",
        "passed": fields_ok,
        "detail": f"Missing fields: {missing}" if missing else "All SolaxSummary fields present."
    })
    if fields_ok:
        total_score += 0.20

    # ── Check 6: values match mock server response ────────────────────────────
    expected = {
        "sn": "SV12345678",
        "inverterType": "X1-Hybrid-G4",
        "acpower": 2650.0,
        "yieldtoday": 18.4,
        "yieldtotal": 4321.7,
        "soc": 73,
        "uploadTime": "2024-06-01 10:30:00"
    }
    value_mismatches = []
    for k, v in expected.items():
        actual = data.get(k)
        if actual != v:
            value_mismatches.append(f"{k}: expected={v!r}, got={actual!r}")

    values_ok = len(value_mismatches) == 0
    checks.append({
        "name": "summary_values_correct",
        "passed": values_ok,
        "detail": "All spot-checked values match mock API." if values_ok else f"Value mismatches: {value_mismatches}"
    })
    if values_ok:
        total_score += 0.20

    return checks, total_score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/home/openclaw/workspace"
    try:
        checks, score = run_eval(workspace)
    except Exception as e:
        checks = [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        score = 0.0

    passed = score >= 0.70
    result = {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()