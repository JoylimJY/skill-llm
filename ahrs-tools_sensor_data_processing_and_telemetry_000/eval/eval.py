import sys
import json
import math
import numpy as np
from pathlib import Path

def load_json_safe(path):
    with open(path, "r") as f:
        return json.load(f)

def main():
    workspace = sys.argv[1]
    checks = []
    overall_passed = True

    # ── locate output file ────────────────────────────────────────────────────
    candidates = list(Path(workspace).rglob("orientation_report.json"))
    if not candidates:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False,
                        "detail": "orientation_report.json not found anywhere in workspace"}]
        }))
        return

    output_path = candidates[0]
    checks.append({"name": "output_file_exists", "passed": True,
                   "detail": str(output_path)})

    # ── load agent output ─────────────────────────────────────────────────────
    try:
        agent_data = load_json_safe(output_path)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "output_parseable", "passed": False,
                                  "detail": f"JSON parse error: {e}"}]
        }))
        return

    checks.append({"name": "output_parseable", "passed": True, "detail": "Valid JSON"})

    # ── load ground truth ─────────────────────────────────────────────────────
    gt_path = Path(workspace) / "telemetry/raw/flight_001/_ground_truth_DO_NOT_EDIT.json"
    try:
        gt_records = load_json_safe(gt_path)
    except Exception as e:
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": checks + [{"name": "ground_truth_readable", "passed": False,
                                  "detail": str(e)}]
        }))
        return

    # ── recompute expected values using pywayne ───────────────────────────────
    try:
        from pywayne.ahrs.tools import quaternion_decompose, quaternion_roll_pitch_compensate
    except ImportError as e:
        print(json.dumps({
            "passed": False, "score": 0.0,
            "checks": checks + [{"name": "pywayne_import", "passed": False,
                                  "detail": str(e)}]
        }))
        return

    expected = []
    for rec in gt_records:
        q = np.array([rec["w"], rec["x"], rec["y"], rec["z"]])
        angle_all, angle_heading, angle_inclination = quaternion_decompose(q)
        q_comp = quaternion_roll_pitch_compensate(q)
        expected.append({
            "timestamp_ms": rec["timestamp_ms"],
            "angle_all": float(angle_all),
            "angle_heading": float(angle_heading),
            "angle_inclination": float(angle_inclination),
            "q_comp": [float(v) for v in q_comp],
        })

    # ── structural check: correct number of records ───────────────────────────
    if not isinstance(agent_data, list):
        checks.append({"name": "output_is_list", "passed": False,
                       "detail": f"Expected a JSON array, got {type(agent_data)}"})
        overall_passed = False
    else:
        checks.append({"name": "output_is_list", "passed": True, "detail": "OK"})
        n_agent = len(agent_data)
        n_expected = len(expected)
        record_count_ok = (n_agent == n_expected)
        checks.append({"name": "record_count", "passed": record_count_ok,
                       "detail": f"agent={n_agent}, expected={n_expected}"})
        if not record_count_ok:
            overall_passed = False

    TOL = 1e-4  # radians / quaternion component tolerance

    # ── per-record checks ─────────────────────────────────────────────────────
    angle_all_ok_count = 0
    angle_heading_ok_count = 0
    angle_inclination_ok_count = 0
    qcomp_ok_count = 0
    ts_ok_count = 0

    if isinstance(agent_data, list) and len(agent_data) == len(expected):
        # Sort both by timestamp to be robust to ordering differences
        try:
            agent_sorted = sorted(agent_data, key=lambda r: r["timestamp_ms"])
        except (KeyError, TypeError):
            agent_sorted = agent_data

        exp_sorted = sorted(expected, key=lambda r: r["timestamp_ms"])

        for i, (ag, ex) in enumerate(zip(agent_sorted, exp_sorted)):
            try:
                # timestamp
                if ag.get("timestamp_ms") == ex["timestamp_ms"]:
                    ts_ok_count += 1

                # angle_all
                if abs(float(ag.get("angle_all", float("nan"))) - ex["angle_all"]) < TOL:
                    angle_all_ok_count += 1

                # angle_heading
                if abs(float(ag.get("angle_heading", float("nan"))) - ex["angle_heading"]) < TOL:
                    angle_heading_ok_count += 1

                # angle_inclination
                if abs(float(ag.get("angle_inclination", float("nan"))) - ex["angle_inclination"]) < TOL:
                    angle_inclination_ok_count += 1

                # compensated quaternion (4 components)
                q_comp_agent = ag.get("q_comp", [])
                if len(q_comp_agent) == 4:
                    diffs = [abs(float(q_comp_agent[j]) - ex["q_comp"][j]) for j in range(4)]
                    if all(d < TOL for d in diffs):
                        qcomp_ok_count += 1
            except Exception:
                pass  # malformed record counts as failure

        n = len(expected)

        def pct(k): return f"{k}/{n}"

        checks.append({"name": "timestamps_correct",
                       "passed": ts_ok_count == n,
                       "detail": pct(ts_ok_count)})
        checks.append({"name": "angle_all_correct",
                       "passed": angle_all_ok_count == n,
                       "detail": pct(angle_all_ok_count)})
        checks.append({"name": "angle_heading_correct",
                       "passed": angle_heading_ok_count == n,
                       "detail": pct(angle_heading_ok_count)})
        checks.append({"name": "angle_inclination_correct",
                       "passed": angle_inclination_ok_count == n,
                       "detail": pct(angle_inclination_ok_count)})
        checks.append({"name": "compensated_quaternion_correct",
                       "passed": qcomp_ok_count == n,
                       "detail": pct(qcomp_ok_count)})

        # All field-level checks must pass
        field_checks = [angle_all_ok_count == n, angle_heading_ok_count == n,
                        angle_inclination_ok_count == n, qcomp_ok_count == n,
                        ts_ok_count == n]
        if not all(field_checks):
            overall_passed = False

    else:
        overall_passed = False

    # ── score ─────────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4) if checks else 0.0

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()