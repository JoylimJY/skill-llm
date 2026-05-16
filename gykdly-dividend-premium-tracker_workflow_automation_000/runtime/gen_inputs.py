import os
import json
import random
import struct
import shutil
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "dividend-premium-tracker/scripts",
    "dividend-premium-tracker/references",
    "dividend-premium-tracker/assets",
    "dividend-premium-tracker/logs",
    "dividend-premium-tracker/archive",
    "dividend-premium-tracker/archive/2025",
    "dividend-premium-tracker/archive/2025/q4",
    "other-trackers/equity-risk",
    "other-trackers/macro-data",
    "reports/monthly",
    "reports/weekly",
    "config",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

BASE = WORKSPACE / "dividend-premium-tracker"

# ── SKILL.md ────────────────────────────────────────────────────────────────
skill_md = """---
name: dividend-premium-tracker
description: Track the dividend premium (dividend yield minus 10-year bond yield) for CSI Dividend Low Volatility Index. Monitor dividend yield, 10-year bond yield, and calculate the premium for investment decisions.
version: 1.0.1
---

# Dividend Premium Tracker

Track the dividend premium for the CSI Dividend Low Volatility Index (H30269), which is crucial for investment decisions in China's dividend-focused market. The dividend premium represents the excess return of dividend-paying stocks over risk-free bonds.

## What It Tracks

- **CSI Dividend Low Volatility Index Dividend Yield** - From China Securities Index
- **10-Year China Government Bond Yield** - From Ministry of Finance
- **Dividend Premium** = Dividend Yield - Bond Yield

## Features

- Auto-download and track dividend and bond yield data
- Generate Excel reports with clean charts
- Alert when bond yield rises for 3 consecutive days
- Alert when premium drops below 1%
- Support for historical data backfill

## Commands

### Update Today's Data
```bash
python3 scripts/update_dividend_premium.py --update
```

### Check Monitoring Alerts
```bash
python3 scripts/monitor_dividend_premium.py --check
```

### Backfill Historical Data
```bash
python3 scripts/update_dividend_premium.py --backfill 2026-01-01 2026-01-31
```

## Files

```
dividend-premium-tracker/
├── SKILL.md
├── scripts/
│   ├── update_dividend_premium.py
│   └── monitor_dividend_premium.py
├── references/
└── assets/
```

## Setup

### Telegram Alerts (Optional)

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
```

### Cron Job (Daily Update)

```bash
crontab -e
# Add line:
0 17 * * * cd /path/to/skill && python3 scripts/update_dividend_premium.py --update
```

## Data Sources

| Data | Source | URL |
|------|--------|-----|
| Dividend Yield | China Securities Index | http://localhost:18765/H30269indicator.xls |
| Bond Yield | Ministry of Finance | http://localhost:18765/bond_yield |

## Alert Thresholds

| Condition | Action |
|-----------|--------|
| Bond yield rises 3 consecutive days | Telegram alert |
| Premium < 1% | Telegram alert |

## Requirements

- Python 3.10+
- pandas
- openpyxl
- xlrd
- curl

## Usage Notes

- Premium is calculated as: `Dividend Yield (%) - Bond Yield (%)`
- Premium < 1% suggests potential buying opportunity
- Premium < 0 indicates dividend stocks are cheaper than bonds
- Historical data from 2026-01-14 to present included
"""
(BASE / "SKILL.md").write_text(skill_md)

# ── Mock XLS data for H30269 indicator ──────────────────────────────────────
# We'll create a realistic XLS file that the mock server will serve.
# The XLS contains: date, dividend_yield columns (as China Securities Index would)
import xlwt

# Build a realistic XLS mimicking H30269indicator.xls
wb = xlwt.Workbook(encoding='utf-8')
ws = wb.add_sheet('Sheet1')

# Header rows (typical CSI format has some metadata rows before data)
ws.write(0, 0, 'H30269 CSI Dividend Low Volatility Index Indicator')
ws.write(1, 0, 'Data Source: China Securities Index Co., Ltd.')
ws.write(2, 0, '')
ws.write(3, 0, '日期')
ws.write(3, 1, '股息率(%)')
ws.write(3, 2, '市盈率')
ws.write(3, 3, '市净率')

# Generate historical data from 2026-01-14 to 2026-03-10
# Simulate realistic dividend yield around 4-6%
start_date = datetime(2026, 1, 14)
end_date = datetime(2026, 3, 10)

date_style = xlwt.XFStyle()
date_style.num_format_str = 'YYYY-MM-DD'

dividend_yields = {}
base_yield = 5.2
current_date = start_date
row = 4
while current_date <= end_date:
    # Skip weekends
    if current_date.weekday() < 5:
        date_str = current_date.strftime('%Y-%m-%d')
        # Small random walk
        base_yield += random.uniform(-0.08, 0.08)
        base_yield = max(3.5, min(7.0, base_yield))
        dy = round(base_yield, 4)
        dividend_yields[date_str] = dy
        ws.write(row, 0, date_str)
        ws.write(row, 1, dy)
        ws.write(row, 2, round(random.uniform(8, 12), 2))
        ws.write(row, 3, round(random.uniform(0.6, 1.2), 2))
        row += 1
    current_date += timedelta(days=1)

xls_path = WORKSPACE / "mock_server_data" / "H30269indicator.xls"
xls_path.parent.mkdir(parents=True, exist_ok=True)
wb.save(str(xls_path))

# ── Bond yield data (JSON for mock server) ──────────────────────────────────
# Simulate 10-year China gov bond yields around 2.0-3.5%
bond_yields = {}
base_bond = 2.8
current_date = start_date
while current_date <= end_date:
    if current_date.weekday() < 5:
        date_str = current_date.strftime('%Y-%m-%d')
        base_bond += random.uniform(-0.04, 0.04)
        base_bond = max(1.8, min(3.8, base_bond))
        bond_yields[date_str] = round(base_bond, 4)
    current_date += timedelta(days=1)

# Force a 3-consecutive-day rise in bond yield near the end (2026-03-06, 03-07, 03-10)
# to trigger the alert
bond_yields['2026-03-06'] = 2.60
bond_yields['2026-03-07'] = 2.65
bond_yields['2026-03-10'] = 2.70

# Force low premium on last day: dividend_yield - bond_yield < 1%
# Set bond yield high so premium < 1%
last_div = dividend_yields.get('2026-03-10', 3.5)
# Make bond yield = last_div - 0.5 to get premium of 0.5 < 1%
bond_yields['2026-03-10'] = round(last_div - 0.5, 4)

bond_data_path = WORKSPACE / "mock_server_data" / "bond_yields.json"
bond_data_path.write_text(json.dumps(bond_yields, indent=2))

# Also save dividend yields for eval reference
div_data_path = WORKSPACE / "mock_server_data" / "dividend_yields.json"
div_data_path.write_text(json.dumps(dividend_yields, indent=2))

# ── The actual scripts ───────────────────────────────────────────────────────

update_script = r'''#!/usr/bin/env python3
"""
update_dividend_premium.py - Download and track dividend premium data.
"""
import argparse
import json
import os
import sys
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_FILE = ASSETS_DIR / "dividend_premium_data.json"
EXCEL_FILE = ASSETS_DIR / "dividend_premium_report.xlsx"

ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Data source URLs (from SKILL.md - can be overridden by env)
DIV_YIELD_URL = os.environ.get(
    "DIV_YIELD_URL",
    "http://localhost:18765/H30269indicator.xls"
)
BOND_YIELD_URL = os.environ.get(
    "BOND_YIELD_URL",
    "http://localhost:18765/bond_yield"
)


def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return {}


def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def download_dividend_yields() -> dict:
    """Download H30269 dividend yield XLS and parse it."""
    import xlrd
    with tempfile.NamedTemporaryFile(suffix=".xls", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", tmp_path, DIV_YIELD_URL],
            capture_output=True, timeout=30
        )
        if result.returncode != 0:
            print(f"[ERROR] curl failed: {result.stderr.decode()}", file=sys.stderr)
            return {}
        book = xlrd.open_workbook(tmp_path)
        sheet = book.sheet_by_index(0)
        yields = {}
        # Find header row (row with '日期')
        header_row = None
        for i in range(min(10, sheet.nrows)):
            for j in range(sheet.ncols):
                cell = str(sheet.cell_value(i, j))
                if '日期' in cell or 'date' in cell.lower():
                    header_row = i
                    break
            if header_row is not None:
                break
        if header_row is None:
            print("[ERROR] Could not find header row in XLS", file=sys.stderr)
            return {}
        # Find column indices
        date_col = None
        yield_col = None
        for j in range(sheet.ncols):
            cell = str(sheet.cell_value(header_row, j))
            if '日期' in cell or 'date' in cell.lower():
                date_col = j
            if '股息率' in cell or 'dividend' in cell.lower() or 'yield' in cell.lower():
                yield_col = j
        if date_col is None or yield_col is None:
            print(f"[ERROR] date_col={date_col}, yield_col={yield_col}", file=sys.stderr)
            return {}
        for i in range(header_row + 1, sheet.nrows):
            try:
                date_val = sheet.cell_value(i, date_col)
                yield_val = sheet.cell_value(i, yield_col)
                if not date_val or not yield_val:
                    continue
                date_str = str(date_val).strip()
                if len(date_str) == 10 and '-' in date_str:
                    yields[date_str] = float(yield_val)
            except Exception:
                continue
        return yields
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def download_bond_yields(start_date: str = None, end_date: str = None) -> dict:
    """Download 10-year bond yield data."""
    import urllib.request
    url = BOND_YIELD_URL
    if start_date and end_date:
        url += f"?start={start_date}&end={end_date}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return data
    except Exception as e:
        print(f"[ERROR] Bond yield download failed: {e}", file=sys.stderr)
        return {}


def generate_excel_report(data: dict):
    """Generate Excel report with dividend premium data."""
    if not data:
        print("[WARN] No data to generate report", file=sys.stderr)
        return
    rows = []
    for date_str, vals in sorted(data.items()):
        rows.append({
            "Date": date_str,
            "Dividend Yield (%)": vals.get("dividend_yield"),
            "Bond Yield (%)": vals.get("bond_yield"),
            "Premium (%)": vals.get("premium"),
        })
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(EXCEL_FILE, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Dividend Premium", index=False)
    print(f"[INFO] Excel report saved: {EXCEL_FILE}")


def do_update():
    """Update today's data."""
    today = datetime.now().strftime('%Y-%m-%d')
    data = load_data()
    print(f"[INFO] Updating data for {today}...")
    div_yields = download_dividend_yields()
    bond_yields = download_bond_yields(today, today)
    if today in div_yields and today in bond_yields:
        dy = div_yields[today]
        by = bond_yields[today]
        premium = round(dy - by, 4)
        data[today] = {
            "dividend_yield": dy,
            "bond_yield": by,
            "premium": premium
        }
        save_data(data)
        generate_excel_report(data)
        print(f"[INFO] Date={today}, DivYield={dy}%, BondYield={by}%, Premium={premium}%")
    else:
        print(f"[WARN] Missing data for {today}. DivYield keys available: {len(div_yields)}, BondYield keys: {len(bond_yields)}")


def do_backfill(start_str: str, end_str: str):
    """Backfill historical data between start_date and end_date (inclusive)."""
    try:
        start = datetime.strptime(start_str, '%Y-%m-%d')
        end = datetime.strptime(end_str, '%Y-%m-%d')
    except ValueError as e:
        print(f"[ERROR] Invalid date format: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Backfilling data from {start_str} to {end_str}...")
    data = load_data()
    div_yields = download_dividend_yields()
    bond_yields = download_bond_yields(start_str, end_str)

    filled = 0
    current = start
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        if date_str in div_yields and date_str in bond_yields:
            dy = div_yields[date_str]
            by = bond_yields[date_str]
            premium = round(dy - by, 4)
            data[date_str] = {
                "dividend_yield": dy,
                "bond_yield": by,
                "premium": premium
            }
            filled += 1
        current += timedelta(days=1)

    save_data(data)
    generate_excel_report(data)
    print(f"[INFO] Backfill complete. {filled} trading days filled.")


def main():
    parser = argparse.ArgumentParser(description="Dividend Premium Tracker - Update Script")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--update", action="store_true", help="Update today's data")
    group.add_argument(
        "--backfill",
        nargs=2,
        metavar=("START_DATE", "END_DATE"),
        help="Backfill data for date range (YYYY-MM-DD YYYY-MM-DD)"
    )
    args = parser.parse_args()
    if args.update:
        do_update()
    elif args.backfill:
        do_backfill(args.backfill[0], args.backfill[1])


if __name__ == "__main__":
    main()
'''

monitor_script = r'''#!/usr/bin/env python3
"""
monitor_dividend_premium.py - Check alert conditions for dividend premium.
"""
import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
BASE_DIR = SCRIPT_DIR.parent
ASSETS_DIR = BASE_DIR / "assets"
DATA_FILE = ASSETS_DIR / "dividend_premium_data.json"
ALERTS_FILE = ASSETS_DIR / "alerts.json"

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

BOND_RISE_DAYS = 3      # consecutive days threshold
PREMIUM_LOW_THRESHOLD = 1.0   # percent


def load_data() -> dict:
    if not DATA_FILE.exists():
        print(f"[ERROR] Data file not found: {DATA_FILE}", file=sys.stderr)
        return {}
    with open(DATA_FILE) as f:
        return json.load(f)


def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[ALERT] (Telegram not configured) {message}")
        return
    import urllib.request
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": message}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[WARN] Telegram send failed: {e}", file=sys.stderr)


def check_alerts(data: dict) -> list:
    """Check all alert conditions. Returns list of triggered alerts."""
    alerts = []
    if not data:
        return alerts

    sorted_dates = sorted(data.keys())
    if not sorted_dates:
        return alerts

    # 1. Check: bond yield rising 3 consecutive days
    if len(sorted_dates) >= BOND_RISE_DAYS:
        consecutive = 0
        for i in range(1, len(sorted_dates)):
            prev_by = data[sorted_dates[i-1]].get("bond_yield", 0)
            curr_by = data[sorted_dates[i]].get("bond_yield", 0)
            if curr_by > prev_by:
                consecutive += 1
                if consecutive >= BOND_RISE_DAYS - 1:
                    alert_msg = (
                        f"[ALERT] Bond yield has risen for {BOND_RISE_DAYS} consecutive days. "
                        f"Latest: {curr_by}% on {sorted_dates[i]}"
                    )
                    alerts.append({
                        "type": "bond_yield_rise",
                        "message": alert_msg,
                        "date": sorted_dates[i],
                        "bond_yield": curr_by,
                        "consecutive_days": BOND_RISE_DAYS
                    })
                    print(alert_msg)
                    send_telegram(alert_msg)
            else:
                consecutive = 0

    # 2. Check: premium < 1% on latest date
    latest_date = sorted_dates[-1]
    latest_premium = data[latest_date].get("premium")
    if latest_premium is not None and latest_premium < PREMIUM_LOW_THRESHOLD:
        alert_msg = (
            f"[ALERT] Dividend premium dropped below {PREMIUM_LOW_THRESHOLD}%: "
            f"{latest_premium}% on {latest_date}"
        )
        alerts.append({
            "type": "premium_low",
            "message": alert_msg,
            "date": latest_date,
            "premium": latest_premium,
            "threshold": PREMIUM_LOW_THRESHOLD
        })
        print(alert_msg)
        send_telegram(alert_msg)

    return alerts


def save_alerts(alerts: list):
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_FILE, "w") as f:
        json.dump({
            "checked_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "alerts": alerts,
            "alert_count": len(alerts)
        }, f, indent=2)
    print(f"[INFO] Alerts saved to {ALERTS_FILE}. Count: {len(alerts)}")


def do_check():
    data = load_data()
    if not data:
        print("[INFO] No data available for monitoring.")
        return
    print(f"[INFO] Checking alerts on {len(data)} data points...")
    alerts = check_alerts(data)
    save_alerts(alerts)
    if not alerts:
        print("[INFO] No alerts triggered.")
    else:
        print(f"[INFO] {len(alerts)} alert(s) triggered.")


def main():
    parser = argparse.ArgumentParser(description="Dividend Premium Monitor")
    parser.add_argument("--check", action="store_true", help="Check alert conditions")
    args = parser.parse_args()
    if args.check:
        do_check()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
'''

(BASE / "scripts" / "update_dividend_premium.py").write_text(update_script)
(BASE / "scripts" / "monitor_dividend_premium.py").write_text(monitor_script)

# ── Distractor files ─────────────────────────────────────────────────────────

# 1. Old archive data (wrong format, stale)
old_archive = {
    "2025-11-03": {"div_yield": 4.9, "bond": 2.7},
    "2025-11-04": {"div_yield": 4.85, "bond": 2.71},
}
(BASE / "archive" / "2025" / "q4" / "old_data.json").write_text(
    json.dumps(old_archive, indent=2)
)

# 2. Stale config with wrong URLs
stale_config = {
    "data_source": "https://old-cdn.csindex.com.cn/H30269.xlsx",
    "bond_source": "https://legacy.chinabond.com.cn/yield",
    "alert_threshold": 2.0,
    "last_update": "2025-12-31"
}
(WORKSPACE / "config" / "tracker_config.json").write_text(
    json.dumps(stale_config, indent=2)
)

# 3. Partial CSV with wrong column names
(BASE / "archive" / "2025" / "partial_export.csv").write_text(
    "date,yield_pct,bond_pct\n2025-10-01,5.1,2.8\n2025-10-02,5.05,2.79\n"
)

# 4. Broken Excel placeholder
(BASE / "assets" / ".gitkeep").write_text("")

# 5. Other tracker distractor
(WORKSPACE / "other-trackers" / "equity-risk" / "config.yaml").write_text(
    "index: CSI300\nrisk_model: barra\nrebalance: monthly\n"
)

# 6. Macro data distractor
(WORKSPACE / "other-trackers" / "macro-data" / "gdp_growth.csv").write_text(
    "quarter,gdp_growth\n2025Q1,5.1\n2025Q2,4.9\n2025Q3,5.0\n2025Q4,4.8\n"
)

# 7. Monthly report placeholder
(WORKSPACE / "reports" / "monthly" / "template.xlsx.placeholder").write_text(
    "Monthly report template - do not modify\n"
)

# 8. Weekly report notes
(WORKSPACE / "reports" / "weekly" / "notes.txt").write_text(
    "Weekly review: check premium threshold on Fridays.\n"
)

# 9. References folder with irrelevant PDF note
(BASE / "references" / "index_methodology.txt").write_text(
    "H30269 CSI Dividend Low Volatility Index Methodology v2.3\n"
    "This document describes the selection criteria and weighting scheme.\n"
    "See official CSIndex website for full document.\n"
)

# 10. Log file from previous run (stale)
(BASE / "logs" / "update_2025-12-31.log").write_text(
    "[INFO] 2025-12-31 17:00:01 - Update complete. 1 record added.\n"
    "[INFO] Premium: 2.31%\n"
)

# 11. A misleading README-like file with WRONG commands
(BASE / "archive" / "DEPRECATED_USAGE.txt").write_text(
    "DEPRECATED - DO NOT USE\n"
    "Old command: python3 scripts/fetch_data.py --date 2025-01-01\n"
    "Old command: python3 scripts/check_alerts.py --threshold 2\n"
)

print("[gen_inputs] Workspace created successfully.")
print(f"[gen_inputs] XLS rows: {len(dividend_yields)} trading days")
print(f"[gen_inputs] Bond yields: {len(bond_yields)} trading days")
print(f"[gen_inputs] Forced 3-day rise: 2026-03-06={bond_yields['2026-03-06']}, "
      f"2026-03-07={bond_yields['2026-03-07']}, 2026-03-10={bond_yields['2026-03-10']}")
last_div = dividend_yields.get('2026-03-10', 'N/A')
last_bond = bond_yields.get('2026-03-10', 'N/A')
if isinstance(last_div, float) and isinstance(last_bond, float):
    print(f"[gen_inputs] Last premium: {round(last_div - last_bond, 4)}% (should be < 1%)")