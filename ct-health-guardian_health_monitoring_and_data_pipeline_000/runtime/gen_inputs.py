import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Directory Structure ---
dirs = [
    "scripts",
    "data",
    "exports/apple_health_2024_01",
    "exports/apple_health_2024_02",
    "exports/apple_health_2024_03",
    "logs",
    "archive/old_configs",
    "archive/old_data",
    "docs",
    "tmp",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor Files ───────────────────────────────────────────────────────

(WORKSPACE / "logs" / "import_2024_01_15.log").write_text(
    "2024-01-15 08:00:01 INFO Starting import\n2024-01-15 08:00:03 INFO Done\n"
)
(WORKSPACE / "logs" / "analyze_2024_01_15.log").write_text(
    "2024-01-15 09:00:01 INFO No anomalies found\n"
)
(WORKSPACE / "archive" / "old_configs" / "config_v0.json").write_text(json.dumps({
    "patient": "Unknown",
    "datasource": "/old/path",
    "temp_max": 101,
    "temp_min": 95,
    "hr_max": 130,
    "hr_min": 45,
    "baseline": 7
}, indent=2))
(WORKSPACE / "archive" / "old_data" / "readings_backup.json").write_text(
    json.dumps({"records": [], "version": "0.1"})
)
(WORKSPACE / "docs" / "setup_notes.txt").write_text(
    "Old setup notes. DO NOT USE.\nSee new skill docs for correct format.\n"
)
(WORKSPACE / "tmp" / "scratch.txt").write_text("temporary workspace\n")
(WORKSPACE / "tmp" / "test_export.json").write_text(
    '{"data": [{"name": "HeartRate", "units": "count/min", "data": []}]}\n'
)
(WORKSPACE / "docs" / "metric_reference.csv").write_text(
    "metric,unit,normal_min,normal_max\nHeartRate,bpm,60,100\nBodyTemperature,degF,97,99\n"
)
(WORKSPACE / "archive" / "old_data" / "alerts_v0.json").write_text(
    json.dumps([{"type": "test", "message": "old alert", "ts": "2024-01-01T00:00:00Z"}])
)

# ─── Broken / Partial config.json (agent must fix) ──────────────────────────
broken_config = {
    "patient_name": "Marcus Rivera",          # wrong key
    "data_source": "./exports",
    "import_interval": "daily",               # wrong value
    "alert_channel": "email",
    "thresholds": {
        "temp_high": 101.0,                   # wrong key names
        "temp_low": 95.0,
        "hr_max": 130,                        # wrong key names
        "hr_min": 45
    }
    # missing baseline_period_days entirely
}
(WORKSPACE / "config.json").write_text(json.dumps(broken_config, indent=2))

# ─── Apple Health Export JSON Files ─────────────────────────────────────────
# Simulate Health Auto Export format: one JSON file per metric group per month

def make_ts(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S +0000")

# Build 30 days of heart rate data: mostly normal, with anomaly at day 25+
BASE_DT = datetime(2024, 3, 1, 8, 0, 0, tzinfo=timezone.utc)

heart_rate_data = []
for day in range(30):
    for hour in [8, 12, 16, 20]:
        dt = BASE_DT + timedelta(days=day, hours=hour - 8)
        # Days 25-29: elevated HR (anomaly)
        if day >= 25:
            val = round(random.uniform(105, 118), 1)
        else:
            val = round(random.uniform(62, 78), 1)
        heart_rate_data.append({
            "date": make_ts(dt),
            "qty": val,
            "source": "Apple Watch"
        })

# Body temperature: mostly normal, fever at day 26-28
body_temp_data = []
for day in range(30):
    dt = BASE_DT + timedelta(days=day, hours=7)
    if 26 <= day <= 28:
        val = round(random.uniform(100.5, 101.3), 1)
    else:
        val = round(random.uniform(97.8, 98.8), 1)
    body_temp_data.append({
        "date": make_ts(dt),
        "qty": val,
        "unit": "degF",
        "source": "Smart Thermometer"
    })

# Sleep duration (hours)
sleep_data = []
for day in range(30):
    dt = BASE_DT + timedelta(days=day, hours=6)
    # Last week: degraded sleep
    if day >= 23:
        val = round(random.uniform(3.8, 5.2), 2)
    else:
        val = round(random.uniform(6.5, 8.2), 2)
    sleep_data.append({
        "date": make_ts(dt),
        "qty": val,
        "unit": "hr",
        "source": "Apple Watch"
    })

# Step count
steps_data = []
for day in range(30):
    dt = BASE_DT + timedelta(days=day, hours=23)
    val = int(random.uniform(200, 800))  # wheelchair user — low step count is normal
    steps_data.append({
        "date": make_ts(dt),
        "qty": val,
        "source": "iPhone"
    })

# SpO2
spo2_data = []
for day in range(30):
    for hour in [8, 20]:
        dt = BASE_DT + timedelta(days=day, hours=hour - 8)
        val = round(random.uniform(95.0, 99.0), 1)
        spo2_data.append({
            "date": make_ts(dt),
            "qty": val,
            "unit": "%",
            "source": "Apple Watch"
        })

# Write export files in Health Auto Export format
export_march = WORKSPACE / "exports" / "apple_health_2024_03"

(export_march / "HeartRate.json").write_text(json.dumps({
    "data": [{"name": "HeartRate", "units": "count/min", "data": heart_rate_data}]
}, indent=2))

(export_march / "BodyTemperature.json").write_text(json.dumps({
    "data": [{"name": "BodyTemperature", "units": "degF", "data": body_temp_data}]
}, indent=2))

(export_march / "SleepAnalysis.json").write_text(json.dumps({
    "data": [{"name": "SleepAnalysis", "units": "hr", "data": sleep_data}]
}, indent=2))

(export_march / "StepCount.json").write_text(json.dumps({
    "data": [{"name": "StepCount", "units": "count", "data": steps_data}]
}, indent=2))

(export_march / "OxygenSaturation.json").write_text(json.dumps({
    "data": [{"name": "OxygenSaturation", "units": "%", "data": spo2_data}]
}, indent=2))

# Older months — sparse/empty data (distractors)
for month in ["apple_health_2024_01", "apple_health_2024_02"]:
    folder = WORKSPACE / "exports" / month
    (folder / "HeartRate.json").write_text(json.dumps({
        "data": [{"name": "HeartRate", "units": "count/min", "data": []}]
    }, indent=2))
    (folder / "BodyTemperature.json").write_text(json.dumps({
        "data": [{"name": "BodyTemperature", "units": "degF", "data": []}]
    }, indent=2))

# ─── Scripts (functional implementations per SKILL.md spec) ─────────────────

import_script = r'''#!/usr/bin/env python3
"""
import_health.py — Imports Apple Health JSON exports into data/readings.json and data/baselines.json
Usage: python3 scripts/import_health.py
Reads config.json for data_source and baseline_period_days.
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse as parse_date

WORKSPACE = Path(__file__).parent.parent
CONFIG_PATH = WORKSPACE / "config.json"
DATA_DIR = WORKSPACE / "data"
DATA_DIR.mkdir(exist_ok=True)

READINGS_PATH = DATA_DIR / "readings.json"
BASELINES_PATH = DATA_DIR / "baselines.json"

REQUIRED_FIELDS = ["human_name", "data_source", "baseline_period_days", "thresholds"]
REQUIRED_THRESHOLD_KEYS = ["temperature_high", "temperature_low", "heart_rate_high", "heart_rate_low"]

def load_config():
    if not CONFIG_PATH.exists():
        print("ERROR: config.json not found", file=sys.stderr)
        sys.exit(1)
    cfg = json.loads(CONFIG_PATH.read_text())
    missing = [f for f in REQUIRED_FIELDS if f not in cfg]
    if missing:
        print(f"ERROR: config.json missing required fields: {missing}", file=sys.stderr)
        sys.exit(2)
    missing_thresh = [k for k in REQUIRED_THRESHOLD_KEYS if k not in cfg.get("thresholds", {})]
    if missing_thresh:
        print(f"ERROR: config.json thresholds missing keys: {missing_thresh}", file=sys.stderr)
        sys.exit(3)
    return cfg

METRIC_MAP = {
    "HeartRate": "heart_rate",
    "BodyTemperature": "temperature",
    "SleepAnalysis": "sleep_duration",
    "StepCount": "steps",
    "OxygenSaturation": "spo2",
}

def import_data(cfg):
    source = Path(cfg["data_source"])
    if not source.is_absolute():
        source = WORKSPACE / source
    
    all_readings = []
    
    # Walk all subdirs for JSON metric files
    for json_file in sorted(source.rglob("*.json")):
        try:
            payload = json.loads(json_file.read_text())
            entries = payload.get("data", [])
            for entry in entries:
                metric_raw = entry.get("name", "")
                metric = METRIC_MAP.get(metric_raw)
                if not metric:
                    continue
                for record in entry.get("data", []):
                    qty = record.get("qty")
                    date_str = record.get("date", "")
                    if qty is None or not date_str:
                        continue
                    try:
                        ts = parse_date(date_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                        all_readings.append({
                            "metric": metric,
                            "value": float(qty),
                            "timestamp": ts.isoformat(),
                            "source": record.get("source", "unknown")
                        })
                    except Exception:
                        continue
        except Exception as e:
            print(f"WARN: skipping {json_file}: {e}", file=sys.stderr)
            continue
    
    all_readings.sort(key=lambda r: r["timestamp"])
    READINGS_PATH.write_text(json.dumps(all_readings, indent=2))
    print(f"Imported {len(all_readings)} readings → {READINGS_PATH}")
    
    # Compute baselines using baseline_period_days from newest data
    baseline_days = int(cfg["baseline_period_days"])
    baselines = compute_baselines(all_readings, baseline_days)
    BASELINES_PATH.write_text(json.dumps(baselines, indent=2))
    print(f"Computed baselines for {len(baselines)} metrics → {BASELINES_PATH}")

def compute_baselines(readings, days):
    if not readings:
        return {}
    # Find cutoff: newest_ts - baseline_days
    newest = max(r["timestamp"] for r in readings)
    try:
        newest_dt = datetime.fromisoformat(newest)
    except Exception:
        newest_dt = datetime.now(tz=timezone.utc)
    if newest_dt.tzinfo is None:
        newest_dt = newest_dt.replace(tzinfo=timezone.utc)
    cutoff = newest_dt - timedelta(days=days)
    
    from collections import defaultdict
    metric_vals = defaultdict(list)
    for r in readings:
        try:
            ts = datetime.fromisoformat(r["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if ts >= cutoff:
            metric_vals[r["metric"]].append(r["value"])
    
    baselines = {}
    for metric, vals in metric_vals.items():
        if not vals:
            continue
        avg = sum(vals) / len(vals)
        variance = sum((v - avg) ** 2 for v in vals) / len(vals)
        std = variance ** 0.5
        baselines[metric] = {
            "mean": round(avg, 3),
            "std": round(std, 3),
            "min": round(min(vals), 3),
            "max": round(max(vals), 3),
            "count": len(vals),
            "period_days": days
        }
    return baselines

if __name__ == "__main__":
    cfg = load_config()
    import_data(cfg)
'''

analyze_script = r'''#!/usr/bin/env python3
"""
analyze.py — Runs pattern detection on stored data, outputs alerts.
Usage: python3 scripts/analyze.py --days 7
Reads config.json, data/readings.json, data/baselines.json.
Writes data/alerts.json and data/patterns.json.
"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

WORKSPACE = Path(__file__).parent.parent
CONFIG_PATH = WORKSPACE / "config.json"
DATA_DIR = WORKSPACE / "data"

READINGS_PATH = DATA_DIR / "readings.json"
BASELINES_PATH = DATA_DIR / "baselines.json"
ALERTS_PATH = DATA_DIR / "alerts.json"
PATTERNS_PATH = DATA_DIR / "patterns.json"

def load_config():
    if not CONFIG_PATH.exists():
        print("ERROR: config.json not found", file=sys.stderr)
        sys.exit(1)
    cfg = json.loads(CONFIG_PATH.read_text())
    missing = [f for f in ["human_name", "thresholds", "baseline_period_days"] if f not in cfg]
    if missing:
        print(f"ERROR: config.json missing: {missing}", file=sys.stderr)
        sys.exit(2)
    required_thresh = ["temperature_high", "temperature_low", "heart_rate_high", "heart_rate_low"]
    missing_t = [k for k in required_thresh if k not in cfg.get("thresholds", {})]
    if missing_t:
        print(f"ERROR: thresholds missing: {missing_t}", file=sys.stderr)
        sys.exit(3)
    return cfg

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=7, help="Number of days to analyze")
    return p.parse_args()

def run_analysis(cfg, days):
    if not READINGS_PATH.exists():
        print("ERROR: data/readings.json not found. Run import_health.py first.", file=sys.stderr)
        sys.exit(4)
    
    readings = json.loads(READINGS_PATH.read_text())
    baselines = json.loads(BASELINES_PATH.read_text()) if BASELINES_PATH.exists() else {}
    
    if not readings:
        print("No readings found.")
        ALERTS_PATH.write_text(json.dumps([], indent=2))
        PATTERNS_PATH.write_text(json.dumps({}, indent=2))
        return
    
    newest = max(r["timestamp"] for r in readings)
    try:
        newest_dt = datetime.fromisoformat(newest)
    except Exception:
        newest_dt = datetime.now(tz=timezone.utc)
    if newest_dt.tzinfo is None:
        newest_dt = newest_dt.replace(tzinfo=timezone.utc)
    cutoff = newest_dt - timedelta(days=days)
    
    recent = [r for r in readings if datetime.fromisoformat(r["timestamp"]).replace(tzinfo=timezone.utc if datetime.fromisoformat(r["timestamp"]).tzinfo is None else None) >= cutoff
              or datetime.fromisoformat(r["timestamp"]).astimezone(timezone.utc) >= cutoff]
    # Re-filter cleanly
    recent = []
    for r in readings:
        try:
            ts = datetime.fromisoformat(r["timestamp"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        if ts >= cutoff:
            recent.append(r)
    
    thresholds = cfg["thresholds"]
    human_name = cfg["human_name"]
    alerts = []
    
    # Group by metric
    by_metric = defaultdict(list)
    for r in recent:
        by_metric[r["metric"]].append(r["value"])
    
    # Temperature checks
    if "temperature" in by_metric:
        temps = by_metric["temperature"]
        avg_temp = sum(temps) / len(temps)
        max_temp = max(temps)
        baseline_mean = baselines.get("temperature", {}).get("mean", avg_temp)
        if max_temp > thresholds["temperature_high"]:
            deviation = round(max_temp - baseline_mean, 2)
            alerts.append({
                "type": "fever_detected",
                "metric": "temperature",
                "human": human_name,
                "current_max": max_temp,
                "baseline_mean": round(baseline_mean, 2),
                "deviation": deviation,
                "threshold": thresholds["temperature_high"],
                "message": (
                    f"🌡️ Temperature Alert\n"
                    f"Current: {max_temp}°F\n"
                    f"Baseline ({cfg['baseline_period_days']}d avg): {round(baseline_mean,1)}°F\n"
                    f"Deviation: +{deviation}°F\n"
                    f"Action: Monitor closely. Consider hydration, check for infection signs."
                ),
                "timestamp": datetime.now(tz=timezone.utc).isoformat()
            })
        if min(temps) < thresholds["temperature_low"]:
            alerts.append({
                "type": "hypothermia_risk",
                "metric": "temperature",
                "human": human_name,
                "current_min": min(temps),
                "threshold": thresholds["temperature_low"],
                "message": f"🌡️ Low Temperature Alert: {min(temps)}°F below safe threshold {thresholds['temperature_low']}°F",
                "timestamp": datetime.now(tz=timezone.utc).isoformat()
            })
    
    # Heart rate checks
    if "heart_rate" in by_metric:
        hrs = by_metric["heart_rate"]
        avg_hr = sum(hrs) / len(hrs)
        max_hr = max(hrs)
        min_hr = min(hrs)
        baseline_mean = baselines.get("heart_rate", {}).get("mean", avg_hr)
        if max_hr > thresholds["heart_rate_high"]:
            deviation = round(((max_hr - baseline_mean) / baseline_mean) * 100, 1)
            alerts.append({
                "type": "tachycardia_risk",
                "metric": "heart_rate",
                "human": human_name,
                "current_max": max_hr,
                "baseline_mean": round(baseline_mean, 1),
                "deviation_pct": deviation,
                "threshold": thresholds["heart_rate_high"],
                "message": f"❤️ High Heart Rate: {max_hr} bpm exceeds threshold {thresholds['heart_rate_high']} bpm (+{deviation}% from baseline)",
                "timestamp": datetime.now(tz=timezone.utc).isoformat()
            })
        if min_hr < thresholds["heart_rate_low"]:
            alerts.append({
                "type": "bradycardia_risk",
                "metric": "heart_rate",
                "human": human_name,
                "current_min": min_hr,
                "threshold": thresholds["heart_rate_low"],
                "message": f"❤️ Low Heart Rate: {min_hr} bpm below threshold {thresholds['heart_rate_low']} bpm",
                "timestamp": datetime.now(tz=timezone.utc).isoformat()
            })
    
    # Sleep degradation check
    if "sleep_duration" in by_metric:
        sleep_vals = by_metric["sleep_duration"]
        avg_sleep = sum(sleep_vals) / len(sleep_vals)
        baseline_sleep = baselines.get("sleep_duration", {}).get("mean", avg_sleep)
        if baseline_sleep > 0:
            deviation_pct = ((avg_sleep - baseline_sleep) / baseline_sleep) * 100
            if deviation_pct < -20:  # more than 20% degradation
                alerts.append({
                    "type": "sleep_degradation",
                    "metric": "sleep_duration",
                    "human": human_name,
                    "recent_avg_hours": round(avg_sleep, 2),
                    "baseline_avg_hours": round(baseline_sleep, 2),
                    "deviation_pct": round(deviation_pct, 1),
                    "message": (
                        f"😴 Sleep Degradation Detected\n"
                        f"Recent avg: {round(avg_sleep,1)}h\n"
                        f"Baseline avg: {round(baseline_sleep,1)}h\n"
                        f"Deviation: {round(deviation_pct,1)}%\n"
                        f"Action: Check for pain, stress, medication changes."
                    ),
                    "timestamp": datetime.now(tz=timezone.utc).isoformat()
                })
    
    # Pattern: correlation between fever and HR elevation
    patterns = {}
    if "temperature" in by_metric and "heart_rate" in by_metric:
        temp_elevated = sum(1 for v in by_metric["temperature"] if v > 99.5)
        hr_elevated = sum(1 for v in by_metric["heart_rate"] if v > 90)
        if temp_elevated > 0 and hr_elevated > 0:
            patterns["fever_tachycardia_correlation"] = {
                "description": "Concurrent temperature elevation and tachycardia detected — possible systemic infection",
                "temp_elevated_readings": temp_elevated,
                "hr_elevated_readings": hr_elevated,
                "severity": "high" if temp_elevated >= 2 else "moderate"
            }
    
    if "sleep_duration" in by_metric and "heart_rate" in by_metric:
        patterns["sleep_hr_trend"] = {
            "description": "Sleep and heart rate monitored for correlation",
            "avg_sleep": round(sum(by_metric["sleep_duration"])/len(by_metric["sleep_duration"]), 2),
            "avg_hr": round(sum(by_metric["heart_rate"])/len(by_metric["heart_rate"]), 2)
        }
    
    ALERTS_PATH.write_text(json.dumps(alerts, indent=2))
    PATTERNS_PATH.write_text(json.dumps(patterns, indent=2))
    
    print(f"Analysis complete: {len(alerts)} alerts, {len(patterns)} patterns detected")
    for a in alerts:
        print(f"  ALERT [{a['type']}]: {a['message'][:80]}...")

if __name__ == "__main__":
    args = parse_args()
    cfg = load_config()
    run_analysis(cfg, args.days)
'''

summary_script = r'''#!/usr/bin/env python3
"""
summary.py — Generates human-readable health summary.
Usage: python3 scripts/summary.py --period week
Reads config.json and all data/ files.
Writes output to stdout AND saves as data/latest_summary.txt
"""
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict

WORKSPACE = Path(__file__).parent.parent
CONFIG_PATH = WORKSPACE / "config.json"
DATA_DIR = WORKSPACE / "data"

def load_config():
    if not CONFIG_PATH.exists():
        print("ERROR: config.json not found", file=sys.stderr)
        sys.exit(1)
    cfg = json.loads(CONFIG_PATH.read_text())
    return cfg

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--period", choices=["day", "week", "month"], default="week",
                   help="Summary period")
    return p.parse_args()

def run_summary(cfg, period):
    period_days = {"day": 1, "week": 7, "month": 30}[period]
    human_name = cfg.get("human_name", "Unknown")
    
    readings_path = DATA_DIR / "readings.json"
    alerts_path = DATA_DIR / "alerts.json"
    baselines_path = DATA_DIR / "baselines.json"
    patterns_path = DATA_DIR / "patterns.json"
    
    readings = json.loads(readings_path.read_text()) if readings_path.exists() else []
    alerts = json.loads(alerts_path.read_text()) if alerts_path.exists() else []
    baselines = json.loads(baselines_path.read_text()) if baselines_path.exists() else {}
    patterns = json.loads(patterns_path.read_text()) if patterns_path.exists() else {}
    
    if readings:
        newest = max(r["timestamp"] for r in readings)
        try:
            newest_dt = datetime.fromisoformat(newest)
            if newest_dt.tzinfo is None:
                newest_dt = newest_dt.replace(tzinfo=timezone.utc)
        except Exception:
            newest_dt = datetime.now(tz=timezone.utc)
        cutoff = newest_dt - timedelta(days=period_days)
        
        recent = []
        for r in readings:
            try:
                ts = datetime.fromisoformat(r["timestamp"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                if ts >= cutoff:
                    recent.append(r)
            except Exception:
                continue
    else:
        recent = []
    
    by_metric = defaultdict(list)
    for r in recent:
        by_metric[r["metric"]].append(r["value"])
    
    lines = []
    lines.append(f"═══════════════════════════════════════════")
    lines.append(f"  HEALTH GUARDIAN — {period.upper()} SUMMARY")
    lines.append(f"  Patient: {human_name}")
    lines.append(f"  Generated: {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"  Period: Last {period_days} day(s)")
    lines.append(f"═══════════════════════════════════════════")
    lines.append("")
    
    lines.append("📊 VITAL SIGNS SUMMARY")
    lines.append("─────────────────────")
    
    metric_display = {
        "heart_rate": ("Heart Rate", "bpm"),
        "temperature": ("Body Temperature", "°F"),
        "sleep_duration": ("Sleep Duration", "hrs"),
        "steps": ("Step Count", "steps"),
        "spo2": ("SpO2", "%"),
    }
    
    for metric_key, (display_name, unit) in metric_display.items():
        if metric_key in by_metric:
            vals = by_metric[metric_key]
            avg = sum(vals) / len(vals)
            baseline = baselines.get(metric_key, {}).get("mean", None)
            line = f"  {display_name}: avg {round(avg,1)} {unit} (n={len(vals)})"
            if baseline:
                diff = avg - baseline
                direction = "↑" if diff > 0.5 else ("↓" if diff < -0.5 else "→")
                line += f" | baseline {round(baseline,1)} {direction}"
            lines.append(line)
        else:
            lines.append(f"  {display_name}: no data")
    
    lines.append("")
    lines.append(f"🚨 ALERTS ({len(alerts)} total)")
    lines.append("─────────────────────")
    if alerts:
        for a in alerts:
            lines.append(f"  [{a.get('type','unknown').upper()}] {a.get('message','').splitlines()[0]}")
    else:
        lines.append("  No alerts triggered.")
    
    lines.append("")
    lines.append(f"🔍 PATTERNS DETECTED ({len(patterns)} total)")
    lines.append("─────────────────────────────────────")
    if patterns:
        for k, v in patterns.items():
            lines.append(f"  [{k}] {v.get('description','')}")
    else:
        lines.append("  No patterns detected.")
    
    lines.append("")
    lines.append(f"📈 BASELINE METRICS (last {cfg.get('baseline_period_days', '?')} days)")
    lines.append("───────────────────────────────────────")
    for metric_key, (display_name, unit) in metric_display.items():
        if metric_key in baselines:
            b = baselines[metric_key]
            lines.append(
                f"  {display_name}: mean={b['mean']} {unit}, "
                f"std=±{b['std']}, range=[{b['min']}, {b['max']}]"
            )
    
    lines.append("")
    lines.append(f"Total readings in period: {len(recent)}")
    lines.append(f"─────────────────────────────────────────")
    
    summary_text = "\n".join(lines)
    print(summary_text)
    
    # Save to data/
    out_path = DATA_DIR / "latest_summary.txt"
    out_path.write_text(summary_text)
    print(f"\nSummary saved to {out_path}", file=sys.stderr)
    
    return summary_text

if __name__ == "__main__":
    args = parse_args()
    cfg = load_config()
    run_summary(cfg, args.period)
'''

(WORKSPACE / "scripts" / "import_health.py").write_text(import_script)
(WORKSPACE / "scripts" / "analyze.py").write_text(analyze_script)
(WORKSPACE / "scripts" / "summary.py").write_text(summary_script)

# Make data dir exist but empty (agent must populate it)
(WORKSPACE / "data" / ".gitkeep").write_text("")

print("Workspace initialized successfully.")
print(f"Files created in {WORKSPACE}:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")