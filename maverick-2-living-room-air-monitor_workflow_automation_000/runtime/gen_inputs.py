#!/usr/bin/env python3
"""
Generate the sandbox workspace for the living-room-air-monitor evaluation task.
Creates a realistic, deeply nested workspace with distractor files and a pre-seeded SQLite DB.
"""

import os
import sqlite3
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

# Deterministic seed
random.seed(42)

# ── Workspace root ──────────────────────────────────────────────────────────
workspace = Path(os.environ.get("WORKSPACE", "/root/workspace"))

# ── Skill directory structure ───────────────────────────────────────────────
skill_root = workspace / "skills" / "living-room-air-monitor"
scripts_dir = skill_root / "scripts"
data_dir = skill_root / "data"

for d in [scripts_dir, data_dir]:
    d.mkdir(parents=True, exist_ok=True)

# ── Distractor files (10+) ──────────────────────────────────────────────────
distractors = [
    workspace / "skills" / "living-room-smoke-detector" / "scripts" / "detect_smoke.py",
    workspace / "skills" / "living-room-smoke-detector" / "data" / "events.log",
    workspace / "skills" / "living-room-air-monitor" / "archive" / "old_readings_2024.csv",
    workspace / "skills" / "living-room-air-monitor" / "archive" / "migration_notes.txt",
    workspace / "config" / "hub_config.json",
    workspace / "config" / "network_map.yaml",
    workspace / "logs" / "cron_air_quality.log",
    workspace / "logs" / "cron_smoke.log",
    workspace / "tmp" / "staging" / "raw_sensor_dump.json",
    workspace / "tmp" / "staging" / "incomplete_readings.csv",
    workspace / "docs" / "sensor_calibration.md",
    workspace / "docs" / "ikea_dirigera_api_notes.txt",
    workspace / "scripts" / "backup_db.sh",
]

for f in distractors:
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f"# distractor: {f.name}\n# This file is not relevant to the current task.\n")

# Distractor JSON config (wrong schema)
(workspace / "config" / "hub_config.json").write_text(json.dumps({
    "hub_ip": "192.168.1.100",
    "timeout": 30,
    "retry": 3
}, indent=2))

# Old CSV with partial data (distractor)
(workspace / "skills" / "living-room-air-monitor" / "archive" / "old_readings_2024.csv").write_text(
    "datetime,temperature,humidity,pm25,co2\n"
    "2024-12-01 10:00,22.1,55.0,8.5,720\n"
    "2024-12-01 11:00,22.3,,9.1,\n"  # incomplete - distractor
)

# ── CONTACTS.json (required by skill) ──────────────────────────────────────
(workspace / "CONTACTS.json").write_text(json.dumps({
    "name": "Test User",
    "email": "testuser@example.com",
    "whatsapp": "+61400000000"
}, indent=2))

# ── SQLite Database with seeded data ────────────────────────────────────────
db_path = data_dir / "air_quality.db"

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS air_quality (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    datetime TEXT NOT NULL UNIQUE,
    temperature REAL,
    humidity REAL,
    pm25 REAL,
    co2 REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
cur.execute("CREATE INDEX IF NOT EXISTS idx_datetime ON air_quality(datetime)")

# ── Seed March 2025: hourly readings for the full month ─────────────────────
# Design: varied values that straddle the proprietary thresholds
# PM2.5: mix of Good (≤12), Moderate (12.1–35), Unhealthy (>35)
# CO2:   mix of Good (≤1000), Moderate (1001–2000), Poor (>2000)

def make_reading(dt: datetime, seed_offset: int):
    r = random.Random(seed_offset)
    temp = round(r.uniform(18.0, 26.5), 1)
    hum  = round(r.uniform(40.0, 75.0), 1)
    # PM2.5: 60% Good, 30% Moderate, 10% Unhealthy
    pm_roll = r.random()
    if pm_roll < 0.60:
        pm25 = round(r.uniform(2.0, 12.0), 1)
    elif pm_roll < 0.90:
        pm25 = round(r.uniform(12.1, 35.0), 1)
    else:
        pm25 = round(r.uniform(35.1, 60.0), 1)
    # CO2: 50% Good, 35% Moderate, 15% Poor
    co2_roll = r.random()
    if co2_roll < 0.50:
        co2 = round(r.uniform(400, 1000), 0)
    elif co2_roll < 0.85:
        co2 = round(r.uniform(1001, 2000), 0)
    else:
        co2 = round(r.uniform(2001, 3000), 0)
    return temp, hum, pm25, co2

start_march = datetime(2025, 3, 1, 0, 0, 0)
end_march   = datetime(2025, 3, 31, 23, 0, 0)

rows = []
current = start_march
idx = 0
while current <= end_march:
    temp, hum, pm25, co2 = make_reading(current, idx)
    rows.append((current.strftime("%Y-%m-%d %H:%M:%S"), temp, hum, pm25, co2))
    current += timedelta(hours=1)
    idx += 1

# Also add week 2025-03-10 to 2025-03-16 (already included in March, but ensure coverage)
# Add a small block for February 2025 (distractor month - less data)
start_feb = datetime(2025, 2, 20, 0, 0, 0)
end_feb   = datetime(2025, 2, 28, 23, 0, 0)
current = start_feb
while current <= end_feb:
    temp, hum, pm25, co2 = make_reading(current, idx + 10000)
    rows.append((current.strftime("%Y-%m-%d %H:%M:%S"), temp, hum, pm25, co2))
    current += timedelta(hours=1)
    idx += 1

cur.executemany(
    "INSERT OR IGNORE INTO air_quality (datetime, temperature, humidity, pm25, co2) VALUES (?,?,?,?,?)",
    rows
)
conn.commit()

# Verify
count = cur.execute("SELECT COUNT(*) FROM air_quality").fetchone()[0]
print(f"[gen_inputs] Inserted {count} rows into {db_path}")

conn.close()

# ── Skill scripts (stubs that delegate to real implementations) ─────────────
# Per directive 3: "All scripts mentioned in the SKILL.md already exist in the workspace."
# We create realistic stub scripts that implement the actual functionality
# so the agent can import from them.

# ── query_data.py ────────────────────────────────────────────────────────────
(scripts_dir / "query_data.py").write_text('''\
#!/usr/bin/env python3
"""Query air quality data from SQLite database."""
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path.home() / ".openclaw/workspace/skills/living-room-air-monitor/data/air_quality.db"

def _get_conn():
    return sqlite3.connect(str(DB_PATH))

def get_reading_by_datetime(dt_str):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT datetime, temperature, humidity, pm25, co2 FROM air_quality "
        "ORDER BY ABS(strftime(\'%s\', datetime) - strftime(\'%s\', ?)) LIMIT 1",
        (dt_str,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"datetime": row[0], "temperature": row[1], "humidity": row[2], "pm25": row[3], "co2": row[4]}
    return None

def get_readings_by_interval(start_dt, end_dt):
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT datetime, temperature, humidity, pm25, co2 FROM air_quality "
        "WHERE datetime >= ? AND datetime <= ? ORDER BY datetime",
        (start_dt, end_dt)
    )
    rows = cur.fetchall()
    conn.close()
    return [{"datetime": r[0], "temperature": r[1], "humidity": r[2], "pm25": r[3], "co2": r[4]} for r in rows]

def get_readings_by_day(date_str):
    start = date_str + " 00:00:00"
    end   = date_str + " 23:59:59"
    return get_readings_by_interval(start, end)

def get_readings_by_month(year_month):
    year, month = year_month.split("-")
    from calendar import monthrange
    last_day = monthrange(int(year), int(month))[1]
    start = f"{year_month}-01 00:00:00"
    end   = f"{year_month}-{last_day:02d} 23:59:59"
    return get_readings_by_interval(start, end)

def get_average_by_day(date_str, metric):
    rows = get_readings_by_day(date_str)
    vals = [r[metric] for r in rows if r[metric] is not None]
    return round(sum(vals) / len(vals), 2) if vals else None

def get_average_by_month(year_month, metric):
    rows = get_readings_by_month(year_month)
    vals = [r[metric] for r in rows if r[metric] is not None]
    return round(sum(vals) / len(vals), 2) if vals else None

def get_all_averages_by_day(date_str):
    return {m: get_average_by_day(date_str, m) for m in ["temperature", "humidity", "pm25", "co2"]}

def get_all_averages_by_month(year_month):
    return {m: get_average_by_month(year_month, m) for m in ["temperature", "humidity", "pm25", "co2"]}

def get_date_range():
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT MIN(datetime), MAX(datetime) FROM air_quality")
    row = cur.fetchone()
    conn.close()
    return (row[0], row[1]) if row else (None, None)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--day")
    parser.add_argument("--month")
    parser.add_argument("--avg-day")
    parser.add_argument("--avg-month")
    parser.add_argument("--metric")
    parser.add_argument("--range", action="store_true")
    args = parser.parse_args()

    if args.range:
        print(get_date_range())
    elif args.avg_day:
        if args.metric:
            print(get_average_by_day(args.avg_day, args.metric))
        else:
            print(get_all_averages_by_day(args.avg_day))
    elif args.avg_month:
        if args.metric:
            print(get_average_by_month(args.avg_month, args.metric))
        else:
            print(get_all_averages_by_month(args.avg_month))
    elif args.day:
        for r in get_readings_by_day(args.day):
            print(r)
    elif args.month:
        for r in get_readings_by_month(args.month):
            print(r)
''')

# ── generate_chart.py ────────────────────────────────────────────────────────
(scripts_dir / "generate_chart.py").write_text('''\
#!/usr/bin/env python3
"""Generate line charts for air quality data."""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.query_data import get_readings_by_interval, get_readings_by_day, get_readings_by_month

DEFAULT_OUTPUT = "/tmp/air_charts"

def generate_chart(start_dt, end_dt, output_path, title="Air Quality"):
    rows = get_readings_by_interval(start_dt, end_dt)
    if not rows:
        print(f"No data for {start_dt} to {end_dt}")
        return None
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if HAS_MPL:
        dates = [datetime.strptime(r["datetime"], "%Y-%m-%d %H:%M:%S") for r in rows]
        fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)
        metrics = ["temperature", "humidity", "pm25", "co2"]
        labels  = ["Temperature (°C)", "Humidity (%)", "PM2.5 (µg/m³)", "CO2 (ppm)"]
        for ax, metric, label in zip(axes, metrics, labels):
            vals = [r[metric] for r in rows]
            ax.plot(dates, vals, linewidth=1)
            ax.set_ylabel(label, fontsize=8)
            ax.grid(True, alpha=0.3)
        axes[0].set_title(title)
        axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
        plt.tight_layout()
        plt.savefig(output_path, dpi=100)
        plt.close()
    else:
        # Write a placeholder text file if matplotlib missing
        Path(output_path).write_text(f"Chart placeholder: {title}\\n{start_dt} to {end_dt}\\n{len(rows)} readings\\n")
    return output_path

def generate_day_chart(date_str, output_dir=DEFAULT_OUTPUT):
    out = str(Path(output_dir) / f"air_{date_str}.png")
    return generate_chart(date_str + " 00:00:00", date_str + " 23:59:59", out, f"Air Quality - {date_str}")

def generate_week_chart(end_date_str, output_dir=DEFAULT_OUTPUT):
    end   = datetime.strptime(end_date_str, "%Y-%m-%d")
    start = end - timedelta(days=6)
    out   = str(Path(output_dir) / f"air_week_{end_date_str}.png")
    return generate_chart(start.strftime("%Y-%m-%d 00:00:00"), end.strftime("%Y-%m-%d 23:59:59"), out,
                          f"Air Quality Week ending {end_date_str}")

def generate_month_chart(year, month, output_dir=DEFAULT_OUTPUT):
    from calendar import monthrange
    last = monthrange(int(year), int(month))[1]
    ym   = f"{year}-{int(month):02d}"
    out  = str(Path(output_dir) / f"air_{ym}.png")
    return generate_chart(f"{ym}-01 00:00:00", f"{ym}-{last:02d} 23:59:59", out, f"Air Quality - {ym}")

def generate_3month_chart(end_date_str, output_dir=DEFAULT_OUTPUT):
    end   = datetime.strptime(end_date_str, "%Y-%m-%d")
    start = end - timedelta(days=89)
    out   = str(Path(output_dir) / f"air_3month_{end_date_str}.png")
    return generate_chart(start.strftime("%Y-%m-%d 00:00:00"), end.strftime("%Y-%m-%d 23:59:59"), out,
                          f"Air Quality 3 Months ending {end_date_str}")

def generate_6month_chart(end_date_str, output_dir=DEFAULT_OUTPUT):
    end   = datetime.strptime(end_date_str, "%Y-%m-%d")
    start = end - timedelta(days=181)
    out   = str(Path(output_dir) / f"air_6month_{end_date_str}.png")
    return generate_chart(start.strftime("%Y-%m-%d 00:00:00"), end.strftime("%Y-%m-%d 23:59:59"), out,
                          f"Air Quality 6 Months ending {end_date_str}")

def generate_year_chart(year, output_dir=DEFAULT_OUTPUT):
    out = str(Path(output_dir) / f"air_{year}.png")
    return generate_chart(f"{year}-01-01 00:00:00", f"{year}-12-31 23:59:59", out, f"Air Quality Year {year}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--day")
    parser.add_argument("--week")
    parser.add_argument("--month")
    parser.add_argument("--3month", dest="three_month")
    parser.add_argument("--6month", dest="six_month")
    parser.add_argument("--year")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.day:
        print(generate_day_chart(args.day, args.output))
    elif args.week:
        print(generate_week_chart(args.week, args.output))
    elif args.month:
        y, m = args.month.split("-")
        print(generate_month_chart(y, m, args.output))
    elif args.three_month:
        print(generate_3month_chart(args.three_month, args.output))
    elif args.six_month:
        print(generate_6month_chart(args.six_month, args.output))
    elif args.year:
        print(generate_year_chart(args.year, args.output))
    else:
        from datetime import date
        print(generate_day_chart(str(date.today()), args.output))
''')

# ── send_report.py ────────────────────────────────────────────────────────────
(scripts_dir / "send_report.py").write_text('''\
#!/usr/bin/env python3
"""Send air quality reports via email or WhatsApp."""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from calendar import monthrange

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.query_data import (
    get_readings_by_interval,
    get_all_averages_by_day,
    get_all_averages_by_month,
)

CONTACTS_PATH = Path.home() / ".openclaw/workspace/CONTACTS.json"

def _load_contacts():
    if CONTACTS_PATH.exists():
        return json.loads(CONTACTS_PATH.read_text())
    return {}

def _pm25_assessment(val):
    if val is None:
        return "Unknown"
    if val <= 12:
        return "Good"
    elif val <= 35:
        return "Moderate"
    else:
        return "Unhealthy"

def _co2_assessment(val):
    if val is None:
        return "Unknown"
    if val <= 1000:
        return "Good"
    elif val <= 2000:
        return "Moderate"
    else:
        return "Poor"

def generate_text_report(start_dt, end_dt):
    readings = get_readings_by_interval(start_dt, end_dt)
    if not readings:
        return f"No data found between {start_dt} and {end_dt}."

    temps  = [r["temperature"] for r in readings if r["temperature"] is not None]
    hums   = [r["humidity"]    for r in readings if r["humidity"]    is not None]
    pm25s  = [r["pm25"]        for r in readings if r["pm25"]        is not None]
    co2s   = [r["co2"]         for r in readings if r["co2"]         is not None]

    avg_temp  = round(sum(temps) / len(temps),  2) if temps  else None
    avg_hum   = round(sum(hums)  / len(hums),   2) if hums   else None
    avg_pm25  = round(sum(pm25s) / len(pm25s),  2) if pm25s  else None
    avg_co2   = round(sum(co2s)  / len(co2s),   2) if co2s   else None

    lines = [
        f"Air Quality Report",
        f"Period: {start_dt} to {end_dt}",
        f"Total readings: {len(readings)}",
        f"",
        f"=== AVERAGES ===",
        f"Temperature : {avg_temp} °C  (range: {min(temps):.1f} – {max(temps):.1f})",
        f"Humidity    : {avg_hum} %   (range: {min(hums):.1f} – {max(hums):.1f})",
        f"PM2.5       : {avg_pm25} µg/m³  (range: {min(pm25s):.1f} – {max(pm25s):.1f})",
        f"CO2         : {avg_co2} ppm  (range: {min(co2s):.0f} – {max(co2s):.0f})",
        f"",
        f"=== AIR QUALITY ASSESSMENT ===",
        f"PM2.5 : {_pm25_assessment(avg_pm25)}",
        f"CO2   : {_co2_assessment(avg_co2)}",
        f"",
        f"=== INDIVIDUAL READINGS ===",
    ]
    for r in readings:
        lines.append(
            f"{r[\'datetime\']}  temp={r[\'temperature\']}  hum={r[\'humidity\']}  pm25={r[\'pm25\']}  co2={r[\'co2\']}"
        )
    return "\\n".join(lines)

def send_report(start_dt, end_dt, channel="email", include_chart=True, chart_path=None):
    contacts = _load_contacts()
    report   = generate_text_report(start_dt, end_dt)
    print(f"[send_report] channel={channel}, to={contacts.get(channel, contacts.get(\'email\', \'??\'))}")
    print(report[:500] + "..." if len(report) > 500 else report)
    # In production: would call gog/wacli here
    return report

def send_daily_report(date_str, channel="email"):
    return send_report(date_str + " 00:00:00", date_str + " 23:59:59", channel)

def send_weekly_report(end_date_str, channel="email"):
    end   = datetime.strptime(end_date_str, "%Y-%m-%d")
    start = end - timedelta(days=6)
    return send_report(start.strftime("%Y-%m-%d 00:00:00"), end.strftime("%Y-%m-%d 23:59:59"), channel)

def send_monthly_report(year, month, channel="email"):
    last = monthrange(int(year), int(month))[1]
    ym   = f"{year}-{int(month):02d}"
    return send_report(f"{ym}-01 00:00:00", f"{ym}-{last:02d} 23:59:59", channel)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--day")
    parser.add_argument("--week")
    parser.add_argument("--month")
    parser.add_argument("--channel", default="email")
    parser.add_argument("--no-chart", action="store_true")
    args = parser.parse_args()

    if args.day:
        send_daily_report(args.day, args.channel)
    elif args.week:
        send_weekly_report(args.week, args.channel)
    elif args.month:
        y, m = args.month.split("-")
        send_monthly_report(y, m, args.channel)
    else:
        from datetime import date
        send_daily_report(str(date.today()), args.channel)
''')

# ── __init__.py stubs ────────────────────────────────────────────────────────
(scripts_dir / "__init__.py").write_text("")
(skill_root / "__init__.py").write_text("")

# ── Symlink ~/.openclaw → workspace ─────────────────────────────────────────
openclaw_link = Path.home() / ".openclaw" / "workspace"
openclaw_link.parent.mkdir(parents=True, exist_ok=True)
if not openclaw_link.exists():
    openclaw_link.symlink_to(workspace)

print("[gen_inputs] Workspace setup complete.")
print(f"  skill_root : {skill_root}")
print(f"  db_path    : {db_path}")
print(f"  openclaw   : {openclaw_link} -> {workspace}")