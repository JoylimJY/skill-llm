import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a deeply nested, realistic directory structure with distractor files
dirs = [
    "infrastructure/cron",
    "infrastructure/logs",
    "infrastructure/configs",
    "infrastructure/backups",
    "services/gateway/config",
    "services/gateway/logs",
    "services/plugins/installed",
    "services/plugins/cache",
    "operations/maintenance",
    "operations/reports",
    "operations/alerts",
    "docs/runbooks",
    "docs/policies",
    "monitoring/dashboards",
    "monitoring/alerts",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic messy infra files
distractor_files = {
    "infrastructure/cron/old_cron_daily.txt": "30 2 * * * /usr/local/bin/legacy-update.sh",
    "infrastructure/cron/cron_backup.txt": "0 1 * * 7 /opt/backup.sh --full",
    "infrastructure/configs/gateway.conf": "[gateway]\nport=8443\nmax_connections=500\ntimeout=30\n",
    "infrastructure/configs/plugins.yaml": "plugins:\n  - name: dicom-handler\n    version: 3.1.2\n  - name: hl7-bridge\n    version: 2.0.8\n  - name: auth-provider\n    version: 1.5.0\n",
    "infrastructure/logs/update_2024-11-01.log": "ERROR: update failed - connection timeout\nERROR: clawdhub unreachable\n",
    "infrastructure/logs/update_2024-12-15.log": "INFO: openclaw updated to 2025.1.0\nINFO: 2 skills updated\nINFO: 9 skills unchanged\n",
    "infrastructure/backups/config_backup_20241201.tar.gz.stub": "BINARY_PLACEHOLDER",
    "services/gateway/config/tls.conf": "cert=/etc/ssl/hospital.crt\nkey=/etc/ssl/hospital.key\nprotocol=TLSv1.3\n",
    "services/gateway/config/network.conf": "bind=0.0.0.0\nport=8443\nbacklog=128\n",
    "services/gateway/logs/access.log": "2025-01-10 03:30:01 INFO Gateway started\n2025-01-10 04:00:00 INFO Health check OK\n",
    "services/plugins/installed/manifest.json": json.dumps({
        "installed": [
            {"name": "dicom-handler", "version": "3.1.2", "status": "active"},
            {"name": "hl7-bridge", "version": "2.0.8", "status": "active"},
            {"name": "auth-provider", "version": "1.5.0", "status": "inactive"},
            {"name": "audit-logger", "version": "0.9.1", "status": "active"},
        ]
    }, indent=2),
    "services/plugins/cache/download_cache.txt": "dicom-handler-3.1.2.tar.gz\nhl7-bridge-2.0.8.tar.gz\n",
    "operations/maintenance/maintenance_windows.txt": "Every Sunday 04:00-06:00 CET - Full maintenance\nWeekdays 02:00-03:00 CET - Automated checks\n",
    "operations/maintenance/change_log.txt": "2024-12-01: Updated openclaw to 2025.1.0\n2024-11-15: Added dicom-handler plugin\n2024-10-01: Initial deployment\n",
    "operations/reports/monthly_report_dec2024.txt": "OpenClaw version: 2025.1.0\nPlugins: 4 installed, 3 active\nUptime: 99.8%\n",
    "operations/alerts/alert_rules.yaml": "rules:\n  - name: update_failure\n    severity: critical\n    notify: ops-team@hospital.de\n",
    "docs/runbooks/update_runbook.txt": "MANUAL UPDATE PROCEDURE\n1. Notify team\n2. Schedule maintenance window\n3. Run updates\n4. Verify health\n5. Close ticket\n",
    "docs/policies/change_management.txt": "All changes must be scheduled outside business hours.\nTimezone: Europe/Berlin\nNotification lead time: 24 hours\n",
    "monitoring/dashboards/gateway_health.json": json.dumps({
        "dashboard": "Gateway Health",
        "panels": ["CPU", "Memory", "Active Connections", "Update Status"]
    }, indent=2),
    "monitoring/alerts/pagerduty_config.yaml": "service_key: PLACEHOLDER\nseverity_map:\n  critical: page\n  warning: email\n",
}

for filepath, content in distractor_files.items():
    full_path = workspace / filepath
    full_path.write_text(content)

# Create a misleading "almost correct" cron template that has wrong flags
misleading_template = workspace / "infrastructure/cron/template_attempt.txt"
misleading_template.write_text(
    "# INCOMPLETE ATTEMPT - DO NOT USE\n"
    'openclaw cron add --name "Update Check" --cron "15 2 * * 1-5" --tz "CET" --message "run updates"\n'
    "# Missing: --session, --wake, --deliver flags\n"
    "# Wrong timezone format: should use IANA name not abbreviation\n"
    "# Wrong message: missing step sequence and dry-run flags\n"
)

# Write a fake SKILL.md reference stub (distractor - missing content)
skill_stub = workspace / "docs/runbooks/skill_notes.txt"
skill_stub.write_text(
    "Notes on scheduling:\n"
    "- Use cron syntax for scheduling\n"
    "- Consider timezone differences\n"
    "- Test before production\n"
    "(See actual skill documentation for full details)\n"
)

print("Workspace initialized with distractor files.")
print(f"Files created: {len(list(workspace.rglob('*')))}")