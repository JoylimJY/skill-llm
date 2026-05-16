import os
import random
import datetime

random.seed(42)

workspace = "/workspace"

# --- Directory structure ---
dirs = [
    "skills/us-treasury-tracker/scripts",
    "skills/us-treasury-tracker/logs",
    "skills/us-treasury-tracker/config",
    "skills/us-treasury-tracker/archive",
    "testdata",
    "data/raw/bonds",
    "data/processed",
    "data/reports/2024",
    "data/reports/2025",
    "infra/mock_servers",
    "infra/configs",
    "docs/api",
    "docs/runbooks",
    "pipeline/stages",
    "pipeline/tests",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---

# 1. Old fetch log with previous entries (distractor: wrong format entries mixed in)
old_log_content = """2024-11-10 09:00:00 | append | success | cnbc=4.120 treasury=4.10
2024-11-11 08:45:22 | append | success | cnbc=4.200 treasury=4.19
2024-12-01 10:12:44 | append | partial | cnbc=4.310 treasury=N/A
2025-01-15 07:30:00 | append | success | cnbc=4.250 treasury=4.24
"""
with open(os.path.join(workspace, "skills/us-treasury-tracker/logs/fetch.log"), "w") as f:
    f.write(old_log_content)

# 2. Existing CSV with old data (a previous day entry must be preserved)
yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
two_days_ago = (datetime.date.today() - datetime.timedelta(days=2)).strftime("%Y-%m-%d")
old_csv_content = f"""Date,CNBC_10Y,Treasury_10Y
{two_days_ago},4.201,4.19
{yesterday},4.275,4.26
"""
with open(os.path.join(workspace, "testdata/us_treasury_10y.csv"), "w") as f:
    f.write(old_csv_content)

# 3. fetch_treasury.py — the actual script (based on SKILL.md behavior)
fetch_script = r'''#!/usr/bin/env python3
"""
US 10-Year Treasury Tracker
Fetches 10Y yield from CNBC and Treasury.gov, writes to CSV, logs result.
"""
import requests
from bs4 import BeautifulSoup
import csv
import os
import datetime
import re

CSV_PATH = os.path.join(os.path.dirname(__file__), "../../../testdata/us_treasury_10y.csv")
LOG_PATH = os.path.join(os.path.dirname(__file__), "../logs/fetch.log")
CSV_PATH = os.path.normpath(CSV_PATH)
LOG_PATH = os.path.normpath(LOG_PATH)

def fetch_cnbc():
    try:
        url = "https://www.cnbc.com/quotes/US10Y"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Look for the rate value in the page
        tag = soup.find("span", {"class": "QuoteStrip-lastPrice"})
        if tag:
            val = float(tag.text.strip().replace("%", ""))
            return val
        # Fallback: search for a pattern like 4.334
        match = re.search(r'"last":"([\d.]+)"', resp.text)
        if match:
            return float(match.group(1))
        return None
    except Exception as e:
        print(f"CNBC fetch error: {e}")
        return None

def fetch_treasury():
    try:
        today = datetime.date.today()
        month = today.month
        year = today.year
        url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value={year}{month:02d}"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.find_all("tr")
        last_val = None
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 9:
                try:
                    val = float(cells[8].text.strip())
                    last_val = val
                except:
                    pass
        return last_val
    except Exception as e:
        print(f"Treasury fetch error: {e}")
        return None

def load_csv():
    rows = []
    if not os.path.exists(CSV_PATH):
        return rows
    with open(CSV_PATH, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def save_csv(rows):
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "CNBC_10Y", "Treasury_10Y"])
        writer.writeheader()
        writer.writerows(rows)

def main():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    cnbc_val = fetch_cnbc()
    treasury_val = fetch_treasury()

    if cnbc_val is not None and treasury_val is not None:
        status = "success"
    elif cnbc_val is not None or treasury_val is not None:
        status = "partial"
    else:
        status = "fail"

    rows = load_csv()
    action = "append"
    found = False
    for i, row in enumerate(rows):
        if row["Date"] == today_str:
            action = "overwrite"
            rows[i] = {
                "Date": today_str,
                "CNBC_10Y": str(cnbc_val) if cnbc_val is not None else "",
                "Treasury_10Y": str(treasury_val) if treasury_val is not None else "",
            }
            found = True
            break
    if not found:
        rows.append({
            "Date": today_str,
            "CNBC_10Y": str(cnbc_val) if cnbc_val is not None else "",
            "Treasury_10Y": str(treasury_val) if treasury_val is not None else "",
        })

    save_csv(rows)

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cnbc_log = str(cnbc_val) if cnbc_val is not None else "N/A"
    treasury_log = str(treasury_val) if treasury_val is not None else "N/A"
    log_line = f"{now_str} | {action} | {status} | cnbc={cnbc_log} treasury={treasury_log}\n"

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(log_line)

    print(f"Done: {log_line.strip()}")

if __name__ == "__main__":
    main()
'''
with open(os.path.join(workspace, "skills/us-treasury-tracker/scripts/fetch_treasury.py"), "w") as f:
    f.write(fetch_script)

# 4. Mock server for CNBC and Treasury.gov
mock_server_script = r'''#!/usr/bin/env python3
"""Mock server that impersonates CNBC and Treasury.gov for testing."""
from flask import Flask, request, Response
import sys

app = Flask(__name__)

CNBC_HTML = """
<html><body>
<span class="QuoteStrip-lastPrice">4.334%</span>
<div>US 10 Year Treasury Note</div>
</body></html>
"""

TREASURY_HTML = """
<html><body>
<table>
<tr><th>Date</th><th>1 Mo</th><th>2 Mo</th><th>3 Mo</th><th>4 Mo</th><th>6 Mo</th><th>1 Yr</th><th>2 Yr</th><th>3 Yr</th><th>10 Yr</th><th>20 Yr</th><th>30 Yr</th></tr>
<tr><td>2025-06-01</td><td>5.10</td><td>5.05</td><td>5.01</td><td>4.98</td><td>4.90</td><td>4.70</td><td>4.50</td><td>4.40</td><td>4.31</td><td>4.60</td><td>4.55</td></tr>
</table>
</body></html>
"""

@app.route("/quotes/US10Y", methods=["GET"])
def cnbc_quote():
    return Response(CNBC_HTML, mimetype="text/html")

@app.route("/resource-center/data-chart-center/interest-rates/TextView", methods=["GET"])
def treasury_data():
    return Response(TREASURY_HTML, mimetype="text/html")

@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def catch_all(path):
    host = request.headers.get("Host", "")
    if "cnbc" in host:
        return Response(CNBC_HTML, mimetype="text/html")
    else:
        return Response(TREASURY_HTML, mimetype="text/html")

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    app.run(host="0.0.0.0", port=port, debug=False)
'''
with open(os.path.join(workspace, "infra/mock_servers/mock_treasury_cnbc.py"), "w") as f:
    f.write(mock_server_script)

# 5. Distractor: old config files
with open(os.path.join(workspace, "skills/us-treasury-tracker/config/settings.json"), "w") as f:
    f.write('{"source": "cnbc+treasury", "retry": 3, "timeout": 10}\n')

# 6. Distractor: archive of old scripts
with open(os.path.join(workspace, "skills/us-treasury-tracker/archive/fetch_treasury_v1.py"), "w") as f:
    f.write("# Deprecated v1 script - do not use\n# Uses old API endpoints\n")

# 7. Distractor: raw bond data files
for i in range(3):
    fname = f"bonds_raw_{2024+i}.csv"
    with open(os.path.join(workspace, "data/raw/bonds", fname), "w") as f:
        f.write("date,yield,maturity\n2024-01-01,4.1,10Y\n")

# 8. Distractor: processed data
with open(os.path.join(workspace, "data/processed/monthly_avg_2025.csv"), "w") as f:
    f.write("month,avg_10y_yield\n2025-01,4.22\n2025-02,4.31\n")

# 9. Distractor: pipeline config
with open(os.path.join(workspace, "pipeline/stages/fetch_stage.yaml"), "w") as f:
    f.write("stage: fetch\nscript: fetch_treasury.py\nschedule: daily\n")

# 10. Distractor: docs
with open(os.path.join(workspace, "docs/runbooks/treasury_fetch_runbook.md"), "w") as f:
    f.write("# Treasury Fetch Runbook\nSee SKILL.md for full details.\nRun the fetch script daily.\n")

with open(os.path.join(workspace, "docs/api/treasury_api_notes.txt"), "w") as f:
    f.write("Treasury.gov API endpoint notes (outdated - see scripts for current logic)\n")

# 11. Distractor: infra config
with open(os.path.join(workspace, "infra/configs/hosts_template.txt"), "w") as f:
    f.write("# Template for /etc/hosts overrides during testing\n127.0.0.1 www.cnbc.com cnbc.com\n127.0.0.1 home.treasury.gov\n")

# 12. Distractor: data reports
for year in [2024, 2025]:
    with open(os.path.join(workspace, f"data/reports/{year}/annual_summary.txt"), "w") as f:
        f.write(f"Annual bond yield summary for {year}\nAverage 10Y: 4.{random.randint(10,39)}\n")

print("Workspace generated successfully.")
print(f"CSV pre-populated with entries for {two_days_ago} and {yesterday}")
print("fetch_treasury.py created at skills/us-treasury-tracker/scripts/")
print("Mock server created at infra/mock_servers/mock_treasury_cnbc.py")