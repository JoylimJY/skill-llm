import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create realistic deeply-nested distractor directory structure
dirs = [
    "skills/local-system-info",
    "skills/network-monitor",
    "skills/log-analyzer",
    "config/deployments/prod",
    "config/deployments/staging",
    "reports/archive/2024-Q1",
    "reports/archive/2024-Q2",
    "scripts/maintenance",
    "scripts/monitoring",
    "docs/runbooks",
    "tmp/scratch",
    "tmp/old_reports",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Create the actual sysinfo.py skill script (SKILL.md says it already exists)
sysinfo_content = '''#!/usr/bin/env python3
"""Local System Info Skill - sysinfo.py"""
import json
import sys
import psutil
import argparse

def get_cpu():
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count(logical=True)
    try:
        load = [x / cpu_count for x in psutil.getloadavg()]
    except AttributeError:
        load = [0.0, 0.0, 0.0]
    return {
        "cpu_percent": cpu_percent,
        "cpu_count": cpu_count,
        "load_avg": load
    }

def get_memory():
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    return {
        "total": vm.total,
        "available": vm.available,
        "percent": vm.percent,
        "swap_percent": swap.percent
    }

def get_disk():
    usage = psutil.disk_usage("/")
    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "percent": usage.percent
    }

def get_processes(limit=20):
    procs = []
    for p in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append({
                "pid": info["pid"],
                "name": info["name"],
                "username": info["username"],
                "cpu_percent": info["cpu_percent"] or 0.0,
                "memory_percent": round(info["memory_percent"] or 0.0, 2)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return procs[:limit]

def main():
    parser = argparse.ArgumentParser(description="Local System Info")
    parser.add_argument("action", choices=["summary", "cpu", "memory", "disk", "processes"])
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.action == "summary":
        result = {
            "cpu": get_cpu(),
            "memory": get_memory(),
            "disk": get_disk()
        }
    elif args.action == "cpu":
        result = get_cpu()
    elif args.action == "memory":
        result = get_memory()
    elif args.action == "disk":
        result = get_disk()
    elif args.action == "processes":
        result = get_processes(args.limit)

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''

(workspace / "skills/local-system-info/sysinfo.py").write_text(sysinfo_content)

# Create distractor files in skill directories
(workspace / "skills/network-monitor/netmon.py").write_text("# network monitor placeholder\n")
(workspace / "skills/log-analyzer/logparse.py").write_text("# log analyzer placeholder\n")

# Config distractors
prod_config = {
    "environment": "production",
    "thresholds": {"cpu_warn": 80, "mem_warn": 85, "disk_warn": 90},
    "alert_email": "ops@example.com"
}
(workspace / "config/deployments/prod/thresholds.json").write_text(json.dumps(prod_config, indent=2))

staging_config = {
    "environment": "staging",
    "thresholds": {"cpu_warn": 70, "mem_warn": 75, "disk_warn": 85},
}
(workspace / "config/deployments/staging/thresholds.json").write_text(json.dumps(staging_config, indent=2))

# Old/stale reports as distractors
old_report = {
    "timestamp": "2024-01-15T10:00:00",
    "note": "STALE - do not use",
    "cpu_usage": "45%",
    "memory_usage": "62%"
}
(workspace / "reports/archive/2024-Q1/system_snapshot.json").write_text(json.dumps(old_report, indent=2))
(workspace / "reports/archive/2024-Q2/system_snapshot.json").write_text(json.dumps({"note": "outdated format"}, indent=2))
(workspace / "tmp/old_reports/pre_deploy_check.txt").write_text("CPU: high\nMEM: ok\nDISK: ok\n")

# Scripts distractors
(workspace / "scripts/maintenance/cleanup.sh").write_text("#!/bin/bash\necho 'cleanup'\n")
(workspace / "scripts/monitoring/check_health.sh").write_text("#!/bin/bash\necho 'health check'\n")

# Docs distractors
(workspace / "docs/runbooks/deployment.md").write_text("# Deployment Runbook\nSee config/deployments/ for thresholds.\n")

# A misleading partial output file to confuse naive agents
misleading = {"status": "incomplete", "action_required": "regenerate with correct tool"}
(workspace / "tmp/scratch/partial_metrics.json").write_text(json.dumps(misleading, indent=2))

print("Workspace initialized successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")