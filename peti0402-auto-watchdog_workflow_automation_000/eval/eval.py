import sys
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── Locate HEARTBEAT.md ──────────────────────────────────────────────────────
heartbeat_files = list(Path(workspace).rglob("HEARTBEAT.md"))
if not heartbeat_files:
    check("HEARTBEAT.md exists", False, "No HEARTBEAT.md file found anywhere in workspace")
    # All remaining checks fail
    for name in [
        "HEARTBEAT.md has Crons section",
        "HEARTBEAT.md: consecutiveErrors > 0 threshold",
        "HEARTBEAT.md: cron not running >2 hours alert",
        "HEARTBEAT.md has Processes section",
        "HEARTBEAT.md: log freshness check present",
        "HEARTBEAT.md: restart before alert (fix-first)",
        "HEARTBEAT.md has Gateway section",
        "HEARTBEAT.md: openclaw gateway status command",
        "HEARTBEAT.md has Disk section",
        "HEARTBEAT.md: 10MB log rotation threshold",
        "HEARTBEAT.md: 1GB workspace size alert",
        "HEARTBEAT.md: HEARTBEAT_OK silent state",
        "systemd service file exists",
        "systemd: ExecStart uses node + guardian.js path",
        "systemd: Restart=always",
        "systemd: RestartSec=60",
    ]:
        check(name, False, "HEARTBEAT.md not found; cannot evaluate")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

hb_path = heartbeat_files[0]
try:
    hb_content = hb_path.read_text(encoding="utf-8")
except Exception as e:
    check("HEARTBEAT.md exists", False, f"Could not read HEARTBEAT.md: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

check("HEARTBEAT.md exists", True, f"Found at {hb_path}")

hb_lower = hb_content.lower()

# ── Crons Section ────────────────────────────────────────────────────────────
has_cron_section = bool(re.search(r'#+\s*cron', hb_lower))
check("HEARTBEAT.md has Crons section", has_cron_section,
      "Found '### Crons' section" if has_cron_section else "Missing Cron section header")

# consecutiveErrors > 0 (not > 1, not >= 1, not > 5)
# Accept: consecutiveErrors > 0, consecutiveerrors > 0, consecutive_errors > 0
consecutive_pattern = re.search(
    r'consecutive[_\s-]?errors?\s*[>]\s*0',
    hb_lower
)
check("HEARTBEAT.md: consecutiveErrors > 0 threshold", bool(consecutive_pattern),
      f"Found '{consecutive_pattern.group(0)}'" if consecutive_pattern else
      "Missing or wrong threshold — must be consecutiveErrors > 0 (not >1, not >=1, not >5)")

# Cron not running >2 hours alert
cron_2h = re.search(r'2\s*hour', hb_lower)
check("HEARTBEAT.md: cron not running >2 hours alert",
      bool(cron_2h),
      "Found 2-hour cron alert rule" if cron_2h else
      "Missing '>2 hours not running' cron alert (skill requires exactly 2 hours)")

# ── Processes Section ────────────────────────────────────────────────────────
has_process_section = bool(re.search(r'#+\s*process', hb_lower))
check("HEARTBEAT.md has Processes section", has_process_section,
      "Found Processes section" if has_process_section else "Missing Processes section header")

# Log freshness check (not PID-based)
log_freshness = re.search(r'log.{0,20}(fresh|stale|minute|timestamp|age|updated)', hb_lower)
check("HEARTBEAT.md: log freshness check present", bool(log_freshness),
      f"Found log freshness check: '{log_freshness.group(0)}'" if log_freshness else
      "Missing log freshness monitoring (skill mandates monitoring by log freshness, not PID)")

# Fix first, alert second — restart mentioned before alert in processes section
proc_section_match = re.search(r'#+\s*process.+?(?=#+\s|\Z)', hb_lower, re.DOTALL)
if proc_section_match:
    proc_text = proc_section_match.group(0)
    restart_pos = proc_text.find('restart')
    alert_pos = proc_text.find('alert')
    if restart_pos == -1:
        check("HEARTBEAT.md: restart before alert (fix-first)", False,
              "No 'restart' keyword in Processes section")
    elif alert_pos == -1:
        check("HEARTBEAT.md: restart before alert (fix-first)", False,
              "No 'alert' keyword in Processes section")
    else:
        fix_first = restart_pos < alert_pos
        check("HEARTBEAT.md: restart before alert (fix-first)", fix_first,
              "Restart mentioned before alert (correct fix-first philosophy)" if fix_first else
              f"Alert (pos {alert_pos}) appears before restart (pos {restart_pos}) — violates 'fix first, alert second'")
else:
    check("HEARTBEAT.md: restart before alert (fix-first)", False,
          "Could not locate Processes section to verify ordering")

# ── Gateway Section ──────────────────────────────────────────────────────────
has_gateway_section = bool(re.search(r'#+\s*gateway', hb_lower))
check("HEARTBEAT.md has Gateway section", has_gateway_section,
      "Found Gateway section" if has_gateway_section else "Missing Gateway section header")

gateway_cmd = re.search(r'openclaw\s+gateway\s+status', hb_lower)
check("HEARTBEAT.md: openclaw gateway status command", bool(gateway_cmd),
      f"Found command: '{gateway_cmd.group(0)}'" if gateway_cmd else
      "Missing 'openclaw gateway status' command — skill requires this exact check")

# ── Disk Section ─────────────────────────────────────────────────────────────
has_disk_section = bool(re.search(r'#+\s*disk', hb_lower))
check("HEARTBEAT.md has Disk section", has_disk_section,
      "Found Disk section" if has_disk_section else "Missing Disk section header")

# 10MB threshold for log rotation
log_10mb = re.search(r'10\s*mb', hb_lower)
check("HEARTBEAT.md: 10MB log rotation threshold", bool(log_10mb),
      "Found 10MB log rotation threshold" if log_10mb else
      "Missing '10MB' log rotation rule — skill specifies exactly 10MB, not 50MB or 100MB")

# 1GB workspace size alert
workspace_1gb = re.search(r'1\s*gb', hb_lower)
check("HEARTBEAT.md: 1GB workspace size alert", bool(workspace_1gb),
      "Found 1GB workspace alert threshold" if workspace_1gb else
      "Missing '1GB workspace size' alert — skill specifies exactly 1GB")

# ── Silent/HEARTBEAT_OK ──────────────────────────────────────────────────────
heartbeat_ok = re.search(r'heartbeat.?ok', hb_lower)
check("HEARTBEAT.md: HEARTBEAT_OK silent state", bool(heartbeat_ok),
      "Found HEARTBEAT_OK keyword" if heartbeat_ok else
      "Missing 'HEARTBEAT_OK' keyword — skill mandates this exact token for the silent/healthy state")

# ── systemd Service File ─────────────────────────────────────────────────────
service_files = list(Path(workspace).rglob("*.service"))
# Exclude the distractor
service_files = [f for f in service_files if "old-monitor" not in f.name]

if not service_files:
    check("systemd service file exists", False, "No *.service file found (excluding old-monitor.service)")
    for name in [
        "systemd: ExecStart uses node + guardian.js path",
        "systemd: Restart=always",
        "systemd: RestartSec=60",
    ]:
        check(name, False, "Service file not found")
else:
    svc_path = service_files[0]
    try:
        svc_content = svc_path.read_text(encoding="utf-8")
    except Exception as e:
        check("systemd service file exists", False, f"Could not read service file: {e}")
        for name in ["systemd: ExecStart uses node + guardian.js path", "systemd: Restart=always", "systemd: RestartSec=60"]:
            check(name, False, "Could not read service file")
        svc_content = ""

    check("systemd service file exists", True, f"Found at {svc_path}")

    if svc_content:
        svc_lower = svc_content.lower()

        # ExecStart must reference node and guardian.js
        exec_match = re.search(r'execstart\s*=\s*.+', svc_lower)
        if exec_match:
            exec_line = exec_match.group(0)
            uses_node = 'node' in exec_line
            uses_guardian = 'guardian' in exec_line
            check("systemd: ExecStart uses node + guardian.js path",
                  uses_node and uses_guardian,
                  f"ExecStart line: '{exec_line}'" if (uses_node and uses_guardian) else
                  f"ExecStart line '{exec_line}' must reference 'node' and 'guardian.js'")
        else:
            check("systemd: ExecStart uses node + guardian.js path", False,
                  "No ExecStart directive found in service file")

        # Restart=always
        restart_always = bool(re.search(r'restart\s*=\s*always', svc_lower))
        check("systemd: Restart=always", restart_always,
              "Found Restart=always" if restart_always else
              "Restart directive is missing or not set to 'always' — skill requires Restart=always")

        # RestartSec=60 (not 5, not 30)
        restartsec_match = re.search(r'restartsec\s*=\s*(\d+)', svc_lower)
        if restartsec_match:
            val = int(restartsec_match.group(1))
            correct = (val == 60)
            check("systemd: RestartSec=60", correct,
                  f"RestartSec={val} — correct (60s)" if correct else
                  f"RestartSec={val} — WRONG; skill mandates exactly 60 seconds")
        else:
            check("systemd: RestartSec=60", False,
                  "No RestartSec directive found — skill requires RestartSec=60")

# ── Scoring ──────────────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
total = len(checks)
score = round(len(passed_checks) / total, 4)

# Must pass all critical checks to be considered overall passing
critical = [
    "HEARTBEAT.md: consecutiveErrors > 0 threshold",
    "HEARTBEAT.md: cron not running >2 hours alert",
    "HEARTBEAT.md: 10MB log rotation threshold",
    "HEARTBEAT.md: 1GB workspace size alert",
    "HEARTBEAT.md: openclaw gateway status command",
    "HEARTBEAT.md: HEARTBEAT_OK silent state",
    "systemd: Restart=always",
    "systemd: RestartSec=60",
    "HEARTBEAT.md: restart before alert (fix-first)",
]
critical_passed = all(
    any(c["name"] == crit and c["passed"] for c in checks)
    for crit in critical
)
overall_passed = critical_passed and score >= 0.85

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))