import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── Find media_report.json anywhere in workspace ──────────────────────────────
report_files = list(Path(workspace).rglob("media_report.json"))

if not report_files:
    add_check("report_file_exists", False, "media_report.json not found anywhere in workspace")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

report_path = report_files[0]
add_check("report_file_exists", True, f"Found at {report_path}")

# ── Parse JSON ────────────────────────────────────────────────────────────────
try:
    with open(report_path) as f:
        report = json.load(f)
    add_check("report_valid_json", True, "Parsed successfully")
except Exception as e:
    add_check("report_valid_json", False, f"JSON parse error: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

# ── Check: devices field exists and has 3 entries ─────────────────────────────
try:
    devices = report.get("devices", [])
    if not isinstance(devices, list) or len(devices) == 0:
        # Try top-level list
        if isinstance(report, list):
            devices = report
    
    has_three = len(devices) == 3
    add_check("three_devices_discovered", has_three, 
              f"Found {len(devices)} devices, expected 3")
except Exception as e:
    add_check("three_devices_discovered", False, f"Error checking devices: {e}")
    devices = []

# ── Check: HomePod devices identified correctly ───────────────────────────────
try:
    device_str = json.dumps(report).lower()
    has_dining = "dining room" in device_str
    has_bar = "bar speaker" in device_str
    add_check("homepod_devices_identified", has_dining and has_bar,
              f"dining_room={has_dining}, bar_speaker={has_bar}")
except Exception as e:
    add_check("homepod_devices_identified", False, f"Error: {e}")

# ── Check: Apple TV identified ────────────────────────────────────────────────
try:
    device_str = json.dumps(report).lower()
    has_appletv = "apple tv" in device_str
    add_check("apple_tv_identified", has_appletv,
              f"Apple TV present: {has_appletv}")
except Exception as e:
    add_check("apple_tv_identified", False, f"Error: {e}")

# ── Check: Airfoil connection log shows HomePods were connected via Airfoil ───
# The agent MUST use connect.sh (which uses airfoil.sh), not atvremote for HomePods
try:
    airfoil_log = Path(workspace) / "skills/airfoil/logs/connections.log"
    if airfoil_log.exists():
        log_content = airfoil_log.read_text().lower()
        dining_connected = "connected dining room" in log_content
        bar_connected = "connected bar speaker" in log_content
        add_check("homepods_connected_via_airfoil", dining_connected or bar_connected,
                  f"Airfoil log shows: dining_connected={dining_connected}, bar_connected={bar_connected}. Log: {log_content.strip()[:300]}")
    else:
        add_check("homepods_connected_via_airfoil", False, "Airfoil connections.log not found or not modified")
except Exception as e:
    add_check("homepods_connected_via_airfoil", False, f"Error reading airfoil log: {e}")

# ── Check: Volume set for HomePods via Airfoil ────────────────────────────────
try:
    airfoil_log = Path(workspace) / "skills/airfoil/logs/connections.log"
    if airfoil_log.exists():
        log_content = airfoil_log.read_text().lower()
        has_volume = "volume" in log_content
        # Check that volume value 35 is present (from the evening schedule target)
        # We accept any volume set via airfoil
        add_check("volume_set_via_airfoil", has_volume,
                  f"Airfoil log shows volume commands: {has_volume}. Log snippet: {log_content.strip()[-200:]}")
    else:
        add_check("volume_set_via_airfoil", False, "Airfoil log not found")
except Exception as e:
    add_check("volume_set_via_airfoil", False, f"Error: {e}")

# ── Check: Report contains Apple TV playback state ───────────────────────────
try:
    report_str = json.dumps(report).lower()
    # The agent should have run `atvremote -n "Apple TV 4K" playing` and captured output
    playback_keywords = ["playing", "blue in green", "miles davis", "play state", "music"]
    found_keywords = [kw for kw in playback_keywords if kw in report_str]
    has_playback_info = len(found_keywords) >= 1
    add_check("apple_tv_playback_info_in_report", has_playback_info,
              f"Playback keywords found: {found_keywords}")
except Exception as e:
    add_check("apple_tv_playback_info_in_report", False, f"Error: {e}")

# ── Check: Report contains device addresses/IPs ───────────────────────────────
try:
    report_str = json.dumps(report)
    ips = ["10.0.0.28", "10.0.0.111", "10.0.0.55"]
    found_ips = [ip for ip in ips if ip in report_str]
    has_ips = len(found_ips) >= 2
    add_check("device_ips_in_report", has_ips,
              f"IPs found in report: {found_ips}")
except Exception as e:
    add_check("device_ips_in_report", False, f"Error: {e}")

# ── Check: Report distinguishes device types (HomePod vs Apple TV) ────────────
try:
    report_str = json.dumps(report).lower()
    has_type_distinction = (
        ("homepod" in report_str or "speaker" in report_str) and
        ("apple tv" in report_str or "appletv" in report_str)
    )
    add_check("device_types_distinguished", has_type_distinction,
              f"Report distinguishes HomePod speakers from Apple TV: {has_type_distinction}")
except Exception as e:
    add_check("device_types_distinguished", False, f"Error: {e}")

# ── Score calculation ─────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
total = len(checks)
score = len(passed_checks) / total if total > 0 else 0.0

# Must pass core checks to overall pass
core_checks = [
    "report_file_exists",
    "report_valid_json", 
    "three_devices_discovered",
    "homepods_connected_via_airfoil",
    "apple_tv_playback_info_in_report",
]
core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)

overall_passed = core_passed and score >= 0.7

result = {
    "passed": overall_passed,
    "score": round(score, 3),
    "checks": checks
}
print(json.dumps(result, indent=2))