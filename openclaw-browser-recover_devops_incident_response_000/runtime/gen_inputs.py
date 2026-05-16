import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Deep distractor directory structure ---
dirs = [
    "infrastructure/monitoring/alerts",
    "infrastructure/monitoring/dashboards",
    "infrastructure/gateway/configs",
    "infrastructure/gateway/logs",
    "infrastructure/chrome/profiles/user",
    "infrastructure/chrome/profiles/openclaw",
    "qa/automation/browser_tests",
    "qa/automation/reports",
    "qa/automation/screenshots",
    "qa/pipelines/nightly",
    "qa/pipelines/smoke",
    "ops/runbooks",
    "ops/incident_logs",
    "skills/openclaw-browser-recover/scripts",
    "skills/openclaw-browser-recover/docs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "infrastructure/monitoring/alerts/cpu_alert.yaml": "threshold: 90\naction: page_oncall\n",
    "infrastructure/monitoring/dashboards/gateway_dashboard.json": json.dumps({"panels": ["latency", "error_rate"], "refresh": "5m"}),
    "infrastructure/gateway/configs/gateway.conf": "port=18789\ncontrol_port=18791\nlog_level=info\n",
    "infrastructure/gateway/logs/gateway_2024-01-10.log": "2024-01-10 08:00:01 INFO gateway started\n2024-01-10 08:01:22 WARN slow response on port 18791\n2024-01-10 09:45:13 ERROR port 18791 unresponsive\n",
    "infrastructure/gateway/logs/gateway_2024-01-11.log": "2024-01-11 10:00:00 INFO gateway restarted by operator\n2024-01-11 10:00:05 INFO all ports nominal\n",
    "infrastructure/chrome/profiles/user/prefs.json": json.dumps({"remote_debugging_port": 9222, "profile": "Default"}),
    "infrastructure/chrome/profiles/openclaw/prefs.json": json.dumps({"remote_debugging_port": 9222, "profile": "openclaw"}),
    "qa/automation/browser_tests/test_login.py": "def test_login():\n    # uses browser profile=user\n    pass\n",
    "qa/automation/browser_tests/test_checkout.py": "def test_checkout():\n    # uses browser profile=openclaw\n    pass\n",
    "qa/automation/reports/run_2024-01-10.json": json.dumps({"status": "failed", "reason": "browser timeout", "timestamp": "2024-01-10T09:46:00Z"}),
    "qa/automation/reports/run_2024-01-09.json": json.dumps({"status": "passed", "tests": 47, "timestamp": "2024-01-09T22:00:00Z"}),
    "qa/pipelines/nightly/pipeline.yaml": "steps:\n  - browser_check\n  - run_tests\n  - publish_report\n",
    "qa/pipelines/smoke/smoke.sh": "#!/bin/bash\nbrowser.status profile=user || exit 1\n",
    "ops/runbooks/general_gateway_ops.md": "# Gateway Operations\nFor general gateway issues, contact the infra team.\nDo not restart services without checking current status first.\n",
    "ops/runbooks/chrome_debugging.md": "# Chrome Remote Debugging\nChrome must be launched with --remote-debugging-port=9222\nVerify with: ss -lntp | grep 9222\n",
    "ops/incident_logs/INC-2024-0108.txt": "Incident: Browser tests hung\nRoot cause: Chrome crashed, 9222 not available\nResolution: Restarted Chrome\nDuration: 22 min\n",
    "ops/incident_logs/INC-2024-0105.txt": "Incident: Gateway 18791 unresponsive\nRoot cause: Memory leak in browser-control\nResolution: gateway restart\nDuration: 8 min\n",
}
for fpath, content in distractor_files.items():
    full = workspace / fpath
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content)

# --- The healthcheck script referenced in SKILL.md (stub, exists but is minimal) ---
healthcheck = workspace / "skills/openclaw-browser-recover/scripts/healthcheck.sh"
healthcheck.write_text(
    "#!/bin/bash\n"
    "# OpenClaw Browser Recovery Healthcheck\n"
    "echo '=== Gateway Status ==='\n"
    "openclaw gateway status\n"
    "echo '=== Port Check ==='\n"
    "ss -lntp | egrep '(:18789|:18791|:9222)' || true\n"
)
os.chmod(str(healthcheck), 0o755)

# --- Incident context file (agent should read this for scenario context) ---
incident_context = workspace / "ops/incident_logs/ACTIVE_INCIDENT.txt"
incident_context.write_text(
    "ACTIVE INCIDENT - INC-2024-0201\n"
    "Reported: 2024-02-01 14:32 UTC\n"
    "Symptom: QA nightly browser tests failing with 'browser.status timed out - Do NOT retry'\n"
    "Affected: All browser automation jobs using profile=user\n"
    "On-call: SRE team\n"
    "Action required: Diagnose and recover browser control pipeline. Document findings in recovery_report.json\n"
)

# --- Partial/broken previous recovery attempt (distractor) ---
bad_report = workspace / "ops/incident_logs/failed_recovery_attempt.txt"
bad_report.write_text(
    "Attempted: browser.status profile=user -> timeout\n"
    "Attempted: browser.status profile=user -> timeout\n"
    "Attempted: browser.status profile=user -> timeout\n"
    "NOTE: Kept retrying despite 'Do NOT retry' warning - WRONG APPROACH\n"
    "Attempted: openclaw gateway stop\n"
    "Attempted: openclaw gateway start\n"
    "NOTE: Used stop+start instead of restart - WRONG APPROACH\n"
    "Status: Unresolved\n"
)

print("Workspace generated successfully.")
print(f"Distractor files: {len(distractor_files)}")
print(f"Healthcheck script: {healthcheck}")
print(f"Active incident: {incident_context}")