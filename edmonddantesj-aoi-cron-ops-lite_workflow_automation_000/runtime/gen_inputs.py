import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure with distractors ---
dirs = [
    "skills/aoi-cron-ops-lite/scripts",
    "skills/aoi-cron-ops-lite/tests",
    "skills/aoi-cron-ops-pro/scripts",
    "config/vault",
    "config/legacy",
    "logs/cron",
    "logs/alerts",
    "reports/archive",
    "reports/drafts",
    "infra/terraform",
    "infra/ansible",
    "docs/runbooks",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "skills/aoi-cron-ops-pro/scripts/analyze_cron_jobs_pro.py": "# Pro version - not available in lite\nraise NotImplementedError('Pro only')\n",
    "config/vault/README.txt": "Vault secrets stored here. Do not commit.\n",
    "config/legacy/old_cron_config.yaml": "# Deprecated cron config from 2021\njobs: []\n",
    "logs/cron/cron_2024_01.log": "2024-01-01 00:00:01 [INFO] job:daily_report ran OK\n2024-01-02 00:00:01 [ERROR] job:sync_users FAILED\n",
    "logs/cron/cron_2024_02.log": "2024-02-01 00:00:01 [INFO] job:weekly_digest ran OK\n",
    "logs/alerts/pagerduty_2024.log": "ALERT: sync_users failed 3x in 24h\n",
    "reports/archive/audit_2023_q4.txt": "Q4 2023 audit - all jobs healthy.\n",
    "reports/drafts/draft_notes.txt": "Notes: check billing jobs cadence\n",
    "infra/terraform/main.tf": "# Terraform config placeholder\n",
    "infra/ansible/playbook.yml": "---\n- name: deploy cron config\n  hosts: all\n  tasks: []\n",
    "docs/runbooks/cron_troubleshooting.md": "# Cron Troubleshooting\nSee internal wiki for escalation steps.\n",
    "skills/aoi-cron-ops-lite/tests/test_placeholder.py": "# Tests for analyzer\nimport pytest\n",
}
for rel_path, content in distractors.items():
    with open(os.path.join(WORKSPACE, rel_path), "w") as f:
        f.write(content)

# --- The actual analyze_cron_jobs.py script (simulates the real tool) ---
# This script reads --in <file>, analyzes it, and prints a report.
# It enforces the 10-25 line output, 5 risk categories, and apply plan.
analyzer_script = r'''#!/usr/bin/env python3
"""
AOI Cron Ops Lite - Cron Job Analyzer
Usage: python3 analyze_cron_jobs.py --in <cron_jobs.json>
"""
import argparse
import json
import sys
import os
from collections import defaultdict

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="infile", required=True, help="Path to cron_jobs.json")
    return parser.parse_args()

def analyze(jobs):
    enabled = [j for j in jobs if j.get("enabled", True)]
    disabled = [j for j in jobs if not j.get("enabled", True)]

    risks = []
    apply_plan = []

    # 1. Duplicate purpose detection
    purpose_map = defaultdict(list)
    for j in enabled:
        p = j.get("purpose", "").strip().lower()
        if p:
            purpose_map[p].append(j["name"])
    for purpose, names in purpose_map.items():
        if len(names) > 1:
            risks.append(f"DUPLICATE_PURPOSE: {', '.join(names)} share purpose '{purpose}'")
            for n in names[1:]:
                apply_plan.append(f"PATCH set delivery=none for job '{n}' [NOT APPLIED]")

    # 2. Notification spam
    announce_jobs = [j for j in enabled if "notify" in j.get("purpose","").lower() or "announce" in j.get("purpose","").lower() or j.get("delivery","") == "broadcast"]
    if len(announce_jobs) >= 3:
        risks.append(f"NOTIFICATION_SPAM: {len(announce_jobs)} announcement/notify jobs active")
        for j in announce_jobs[1:]:
            apply_plan.append(f"PATCH change delivery=none for job '{j['name']}' [NOT APPLIED]")

    # 3. Over-frequent cadence (jobs running more often than every 5 minutes)
    heavy = []
    for j in enabled:
        cadence = j.get("cadence_minutes", 60)
        if isinstance(cadence, (int, float)) and cadence < 5:
            heavy.append(j["name"])
    if heavy:
        risks.append(f"HEAVY_CADENCE: {', '.join(heavy)} run more than every 5 min (cost risk)")
        for n in heavy:
            apply_plan.append(f"PATCH slow cadence to 15min for job '{n}' [NOT APPLIED]")

    # 4. Repeated failures
    flaky = [j for j in enabled if j.get("consecutive_failures", 0) >= 3]
    if flaky:
        names = [j["name"] for j in flaky]
        risks.append(f"REPEATED_FAILURES: {', '.join(names)} has >=3 consecutive failures")
        for j in flaky:
            apply_plan.append(f"PATCH set delivery=none for job '{j['name']}' [NOT APPLIED]")

    # 5. Missing env prerequisites
    missing_env = []
    for j in enabled:
        req = j.get("requires_vault_file", None)
        if req and not os.path.exists(req):
            missing_env.append(f"{j['name']} (needs {req})")
    if missing_env:
        risks.append(f"MISSING_ENV: {'; '.join(missing_env)}")
        for item in missing_env:
            name = item.split(" ")[0]
            apply_plan.append(f"PATCH disable job '{name}' until vault file present [NOT APPLIED]")

    return enabled, disabled, risks, apply_plan

def main():
    args = parse_args()
    try:
        with open(args.infile) as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: Cannot read input file: {e}", file=sys.stderr)
        sys.exit(1)

    jobs = data if isinstance(data, list) else data.get("jobs", [])
    enabled, disabled, risks, apply_plan = analyze(jobs)

    lines = []
    lines.append(f"=== AOI Cron Ops Lite Report ===")
    lines.append(f"TOTALS: {len(enabled)+len(disabled)} jobs | {len(enabled)} enabled | {len(disabled)} disabled")
    lines.append("")
    lines.append(f"TOP RISKS ({min(len(risks),5)} of {len(risks)}):")
    for r in risks[:5]:
        lines.append(f"  - {r}")
    if not risks:
        lines.append("  (none detected)")
    lines.append("")
    lines.append("RECOMMENDED ACTIONS:")
    action_groups = {}
    for p in apply_plan:
        key = p.split(" ")[1]  # PATCH keyword group
        action_groups.setdefault(key, []).append(p)
    if action_groups:
        for group, patches in action_groups.items():
            for p in patches:
                lines.append(f"  {p}")
    else:
        lines.append("  (no actions needed)")
    lines.append("")
    lines.append("APPLY PLAN (patches listed, NOT executed - Lite mode):")
    if apply_plan:
        for p in apply_plan:
            lines.append(f"  >> {p}")
    else:
        lines.append("  >> (nothing to apply)")

    # Enforce 10-25 line output
    # Trim if too long
    while len(lines) > 25:
        lines.pop(-2)  # remove from before last line
    # Pad if too short
    while len(lines) < 10:
        lines.append("")

    print("\n".join(lines))

if __name__ == "__main__":
    main()
'''

with open(os.path.join(WORKSPACE, "skills/aoi-cron-ops-lite/scripts/analyze_cron_jobs.py"), "w") as f:
    f.write(analyzer_script)

# --- The messy cron_jobs.json input file ---
# Contains: duplicates, spam notifiers, heavy cadence jobs, repeated failures, missing vault
cron_jobs = [
    {
        "name": "billing_sync_primary",
        "purpose": "sync billing records to data warehouse",
        "enabled": True,
        "cadence_minutes": 60,
        "consecutive_failures": 0,
        "delivery": "email",
        "requires_vault_file": None
    },
    {
        "name": "billing_sync_backup",
        "purpose": "sync billing records to data warehouse",
        "enabled": True,
        "cadence_minutes": 60,
        "consecutive_failures": 0,
        "delivery": "email",
        "requires_vault_file": None
    },
    {
        "name": "billing_sync_legacy",
        "purpose": "sync billing records to data warehouse",
        "enabled": True,
        "cadence_minutes": 120,
        "consecutive_failures": 1,
        "delivery": "none",
        "requires_vault_file": None
    },
    {
        "name": "notify_daily_standup",
        "purpose": "announce daily standup reminder to team channel",
        "enabled": True,
        "cadence_minutes": 1440,
        "consecutive_failures": 0,
        "delivery": "broadcast",
        "requires_vault_file": None
    },
    {
        "name": "notify_sprint_kickoff",
        "purpose": "announce sprint kickoff event",
        "enabled": True,
        "cadence_minutes": 10080,
        "consecutive_failures": 0,
        "delivery": "broadcast",
        "requires_vault_file": None
    },
    {
        "name": "notify_oncall_rotation",
        "purpose": "notify oncall rotation update",
        "enabled": True,
        "cadence_minutes": 10080,
        "consecutive_failures": 0,
        "delivery": "broadcast",
        "requires_vault_file": None
    },
    {
        "name": "notify_deployment_alert",
        "purpose": "announce deployment status",
        "enabled": True,
        "cadence_minutes": 30,
        "consecutive_failures": 0,
        "delivery": "broadcast",
        "requires_vault_file": None
    },
    {
        "name": "metrics_scrape_realtime",
        "purpose": "scrape real-time system metrics",
        "enabled": True,
        "cadence_minutes": 1,
        "consecutive_failures": 0,
        "delivery": "none",
        "requires_vault_file": None
    },
    {
        "name": "heartbeat_ping",
        "purpose": "ping external health endpoint",
        "enabled": True,
        "cadence_minutes": 2,
        "consecutive_failures": 0,
        "delivery": "none",
        "requires_vault_file": None
    },
    {
        "name": "external_payment_reconcile",
        "purpose": "reconcile payment gateway records",
        "enabled": True,
        "cadence_minutes": 360,
        "consecutive_failures": 5,
        "delivery": "email",
        "requires_vault_file": None
    },
    {
        "name": "crm_user_sync",
        "purpose": "sync CRM user data from Salesforce",
        "enabled": True,
        "cadence_minutes": 720,
        "consecutive_failures": 4,
        "delivery": "email",
        "requires_vault_file": None
    },
    {
        "name": "vault_secret_rotation",
        "purpose": "rotate vault secrets for prod services",
        "enabled": True,
        "cadence_minutes": 1440,
        "consecutive_failures": 0,
        "delivery": "email",
        "requires_vault_file": "/workspace/config/vault/prod_secrets.vault"
    },
    {
        "name": "weekly_digest_report",
        "purpose": "send weekly cost digest to finance team",
        "enabled": True,
        "cadence_minutes": 10080,
        "consecutive_failures": 0,
        "delivery": "email",
        "requires_vault_file": None
    },
    {
        "name": "db_backup_nightly",
        "purpose": "nightly database backup to S3",
        "enabled": False,
        "cadence_minutes": 1440,
        "consecutive_failures": 0,
        "delivery": "none",
        "requires_vault_file": None
    },
    {
        "name": "log_archival",
        "purpose": "archive old logs to cold storage",
        "enabled": False,
        "cadence_minutes": 10080,
        "consecutive_failures": 0,
        "delivery": "none",
        "requires_vault_file": None
    }
]

with open(os.path.join(WORKSPACE, "cron_jobs.json"), "w") as f:
    json.dump(cron_jobs, f, indent=2)

# NOTE: /workspace/config/vault/prod_secrets.vault intentionally does NOT exist
# to trigger the MISSING_ENV risk detection.

print("Workspace generated successfully.")
print(f"  - {len(cron_jobs)} cron jobs in cron_jobs.json")
print("  - analyze_cron_jobs.py placed in skills/aoi-cron-ops-lite/scripts/")
print("  - prod_secrets.vault intentionally absent to trigger MISSING_ENV risk")