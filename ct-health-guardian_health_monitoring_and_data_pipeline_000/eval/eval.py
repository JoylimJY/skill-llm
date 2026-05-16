import sys
import json
import os
from pathlib import Path

def run_eval(workspace_dir: str):
    ws = Path(workspace_dir)
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ─── CHECK 1: config.json has correct human_name ─────────────────────────
    try:
        cfg_path = ws / "config.json"
        cfg = json.loads(cfg_path.read_text())
        passed = cfg.get("human_name") == "Marcus Rivera"
        detail = f"human_name={cfg.get('human_name')!r} (expected 'Marcus Rivera')"
        total_score += add_check("config.json: human_name is 'Marcus Rivera'", passed, detail, 0.5)
    except Exception as e:
        total_score += add_check("config.json: human_name is 'Marcus Rivera'", False, f"Error: {e}", 0.5)

    # ─── CHECK 2: config.json has correct threshold keys ─────────────────────
    try:
        cfg_path = ws / "config.json"
        cfg = json.loads(cfg_path.read_text())
        thresh = cfg.get("thresholds", {})
        required_keys = ["temperature_high", "temperature_low", "heart_rate_high", "heart_rate_low"]
        has_all = all(k in thresh for k in required_keys)
        missing = [k for k in required_keys if k not in thresh]
        detail = f"Present keys: {list(thresh.keys())}. Missing: {missing}"
        total_score += add_check("config.json: correct threshold key names", has_all, detail, 1.0)
    except Exception as e:
        total_score += add_check("config.json: correct threshold key names", False, f"Error: {e}", 1.0)

    # ─── CHECK 3: config.json threshold values match SKILL.md defaults ────────
    try:
        cfg_path = ws / "config.json"
        cfg = json.loads(cfg_path.read_text())
        thresh = cfg.get("thresholds", {})
        # Check standard values from SKILL.md
        temp_high_ok = abs(float(thresh.get("temperature_high", 0)) - 100.4) < 0.01
        temp_low_ok  = abs(float(thresh.get("temperature_low", 0)) - 96.0) < 0.01
        hr_high_ok   = abs(float(thresh.get("heart_rate_high", 0)) - 120) < 0.01
        hr_low_ok    = abs(float(thresh.get("heart_rate_low", 0)) - 50) < 0.01
        all_ok = temp_high_ok and temp_low_ok and hr_high_ok and hr_low_ok
        detail = (
            f"temperature_high={thresh.get('temperature_high')} (want 100.4): {temp_high_ok}, "
            f"temperature_low={thresh.get('temperature_low')} (want 96.0): {temp_low_ok}, "
            f"heart_rate_high={thresh.get('heart_rate_high')} (want 120): {hr_high_ok}, "
            f"heart_rate_low={thresh.get('heart_rate_low')} (want 50): {hr_low_ok}"
        )
        total_score += add_check("config.json: threshold values match SKILL.md spec", all_ok, detail, 1.0)
    except Exception as e:
        total_score += add_check("config.json: threshold values match SKILL.md spec", False, f"Error: {e}", 1.0)

    # ─── CHECK 4: config.json has baseline_period_days = 14 ──────────────────
    try:
        cfg_path = ws / "config.json"
        cfg = json.loads(cfg_path.read_text())
        val = cfg.get("baseline_period_days")
        passed = val == 14
        detail = f"baseline_period_days={val!r} (expected 14)"
        total_score += add_check("config.json: baseline_period_days=14", passed, detail, 0.5)
    except Exception as e:
        total_score += add_check("config.json: baseline_period_days=14", False, f"Error: {e}", 0.5)

    # ─── CHECK 5: data/readings.json populated ────────────────────────────────
    try:
        readings_path = ws / "data" / "readings.json"
        if not readings_path.exists():
            total_score += add_check("data/readings.json: exists and has records", False,
                                     "File does not exist", 1.5)
        else:
            readings = json.loads(readings_path.read_text())
            if not isinstance(readings, list):
                total_score += add_check("data/readings.json: exists and has records", False,
                                         f"Expected list, got {type(readings)}", 1.5)
            else:
                has_hr = any(r.get("metric") == "heart_rate" for r in readings)
                has_temp = any(r.get("metric") == "temperature" for r in readings)
                has_sleep = any(r.get("metric") == "sleep_duration" for r in readings)
                passed = len(readings) >= 50 and has_hr and has_temp and has_sleep
                detail = (
                    f"Total readings: {len(readings)}, "
                    f"has_heart_rate={has_hr}, has_temperature={has_temp}, has_sleep={has_sleep}"
                )
                total_score += add_check("data/readings.json: exists and has records", passed, detail, 1.5)
    except Exception as e:
        total_score += add_check("data/readings.json: exists and has records", False, f"Error: {e}", 1.5)

    # ─── CHECK 6: data/baselines.json populated ───────────────────────────────
    try:
        baselines_path = ws / "data" / "baselines.json"
        if not baselines_path.exists():
            total_score += add_check("data/baselines.json: exists and has baseline data", False,
                                     "File does not exist", 1.0)
        else:
            baselines = json.loads(baselines_path.read_text())
            if not isinstance(baselines, dict) or len(baselines) == 0:
                total_score += add_check("data/baselines.json: exists and has baseline data", False,
                                         f"Empty or wrong format: {baselines}", 1.0)
            else:
                # Check that at least heart_rate and temperature baselines exist
                has_hr_baseline = "heart_rate" in baselines
                has_temp_baseline = "temperature" in baselines
                # Check structure of one baseline
                if has_hr_baseline:
                    b = baselines["heart_rate"]
                    has_fields = all(k in b for k in ["mean", "std", "min", "max", "count", "period_days"])
                else:
                    has_fields = False
                passed = has_hr_baseline and has_temp_baseline and has_fields
                detail = (
                    f"Metrics: {list(baselines.keys())}, "
                    f"hr_baseline={has_hr_baseline}, temp_baseline={has_temp_baseline}, "
                    f"correct_fields={has_fields}"
                )
                total_score += add_check("data/baselines.json: exists and has baseline data", passed, detail, 1.0)
    except Exception as e:
        total_score += add_check("data/baselines.json: exists and has baseline data", False, f"Error: {e}", 1.0)

    # ─── CHECK 7: data/alerts.json has fever and/or anomaly alerts ────────────
    try:
        alerts_path = ws / "data" / "alerts.json"
        if not alerts_path.exists():
            total_score += add_check("data/alerts.json: exists and contains anomaly alerts", False,
                                     "File does not exist", 1.5)
        else:
            alerts = json.loads(alerts_path.read_text())
            if not isinstance(alerts, list):
                total_score += add_check("data/alerts.json: exists and contains anomaly alerts", False,
                                         f"Expected list, got {type(alerts)}", 1.5)
            elif len(alerts) == 0:
                total_score += add_check("data/alerts.json: exists and contains anomaly alerts", False,
                                         "No alerts found — anomaly data was present in exports", 1.5)
            else:
                alert_types = {a.get("type") for a in alerts}
                has_fever = any(t in alert_types for t in ["fever_detected", "tachycardia_risk"])
                has_sleep = "sleep_degradation" in alert_types
                passed = has_fever or has_sleep
                detail = (
                    f"Total alerts: {len(alerts)}, types: {list(alert_types)}, "
                    f"has_fever_or_tachy={has_fever}, has_sleep_deg={has_sleep}"
                )
                total_score += add_check("data/alerts.json: exists and contains anomaly alerts", passed, detail, 1.5)
    except Exception as e:
        total_score += add_check("data/alerts.json: exists and contains anomaly alerts", False, f"Error: {e}", 1.5)

    # ─── CHECK 8: data/patterns.json exists ───────────────────────────────────
    try:
        patterns_path = ws / "data" / "patterns.json"
        if not patterns_path.exists():
            total_score += add_check("data/patterns.json: exists", False, "File does not exist", 0.5)
        else:
            patterns = json.loads(patterns_path.read_text())
            passed = isinstance(patterns, dict)
            detail = f"Patterns keys: {list(patterns.keys()) if isinstance(patterns, dict) else 'wrong type'}"
            total_score += add_check("data/patterns.json: exists", passed, detail, 0.5)
    except Exception as e:
        total_score += add_check("data/patterns.json: exists", False, f"Error: {e}", 0.5)

    # ─── CHECK 9: weekly_health_summary.txt exists with real content ──────────
    try:
        # Search for the file anywhere in workspace
        candidates = list(ws.rglob("weekly_health_summary.txt"))
        if not candidates:
            total_score += add_check("weekly_health_summary.txt: exists with meaningful content", False,
                                     "File not found anywhere in workspace", 2.0)
        else:
            summary_path = candidates[0]
            content = summary_path.read_text()
            # Must mention patient name and contain health data
            has_patient = "Marcus Rivera" in content
            has_vitals = any(kw in content for kw in ["Heart Rate", "Temperature", "Sleep", "bpm", "°F"])
            has_alerts_section = "ALERT" in content.upper() or "alert" in content.lower()
            has_period = "WEEK" in content.upper() or "week" in content.lower() or "7 day" in content.lower()
            has_baseline = "baseline" in content.lower() or "BASELINE" in content
            passed = has_patient and has_vitals and has_alerts_section and len(content) > 200
            detail = (
                f"Path: {summary_path.relative_to(ws)}, length={len(content)}, "
                f"has_patient={has_patient}, has_vitals={has_vitals}, "
                f"has_alerts_section={has_alerts_section}, has_period_marker={has_period}, "
                f"has_baseline={has_baseline}"
            )
            total_score += add_check("weekly_health_summary.txt: exists with meaningful content",
                                     passed, detail, 2.0)
    except Exception as e:
        total_score += add_check("weekly_health_summary.txt: exists with meaningful content",
                                 False, f"Error: {e}", 2.0)

    # ─── CHECK 10: Alert human_name field references Marcus Rivera ────────────
    try:
        alerts_path = ws / "data" / "alerts.json"
        alerts = json.loads(alerts_path.read_text()) if alerts_path.exists() else []
        if alerts:
            names_in_alerts = {a.get("human") for a in alerts if a.get("human")}
            passed = "Marcus Rivera" in names_in_alerts
            detail = f"human values in alerts: {names_in_alerts}"
        else:
            passed = False
            detail = "No alerts to check human field"
        total_score += add_check("alerts.json: human field = 'Marcus Rivera'", passed, detail, 0.5)
    except Exception as e:
        total_score += add_check("alerts.json: human field = 'Marcus Rivera'", False, f"Error: {e}", 0.5)

    # ─── Compute final score ─────────────────────────────────────────────────
    max_score = 0.5 + 1.0 + 1.0 + 0.5 + 1.5 + 1.0 + 1.5 + 0.5 + 2.0 + 0.5  # = 10.0
    normalized_score = round(total_score / max_score, 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed and normalized_score >= 0.85,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)