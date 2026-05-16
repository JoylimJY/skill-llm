import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create the skill script structure (as if pre-installed) ---
skill_dir = workspace / "skills" / "local-system-info"
skill_dir.mkdir(parents=True, exist_ok=True)

sysinfo_py = skill_dir / "sysinfo.py"
sysinfo_py.write_text('''\
#!/usr/bin/env python3
"""Local System Info Skill - sysinfo.py"""
import argparse
import json
import psutil
import os

def get_cpu():
    load = psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0.0, 0.0, 0.0]
    cpu_count = psutil.cpu_count(logical=True) or 1
    normalized = [round(l / cpu_count, 4) for l in load]
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "cpu_count": cpu_count,
        "load_avg": normalized
    }

def get_memory():
    vm = psutil.virtual_memory()
    sw = psutil.swap_memory()
    return {
        "total": vm.total,
        "available": vm.available,
        "percent": vm.percent,
        "swap_percent": sw.percent
    }

def get_disk():
    du = psutil.disk_usage("/")
    return {
        "total": du.total,
        "used": du.used,
        "free": du.free,
        "percent": du.percent
    }

def get_processes(limit=20):
    procs = []
    for p in psutil.process_iter(["pid", "name", "username", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            procs.append({
                "pid": info["pid"],
                "name": info["name"] or "",
                "username": info["username"] or "",
                "cpu_percent": info["cpu_percent"] or 0.0,
                "memory_percent": round(info["memory_percent"] or 0.0, 4)
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
''')

# --- Create deeply nested distractor files ---
dirs = [
    workspace / "ops" / "reports" / "2024" / "q1",
    workspace / "ops" / "reports" / "2024" / "q2",
    workspace / "ops" / "alerts" / "cpu",
    workspace / "ops" / "alerts" / "memory",
    workspace / "ops" / "configs" / "thresholds",
    workspace / "monitoring" / "dashboards",
    workspace / "monitoring" / "exporters",
    workspace / "infra" / "ansible" / "roles",
    workspace / "infra" / "terraform" / "modules",
    workspace / "scripts" / "legacy",
]
for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor files — plausible but irrelevant
distractors = [
    (workspace / "ops" / "reports" / "2024" / "q1" / "server_audit_q1.csv",
     "hostname,cpu_avg,ram_used_gb,disk_used_gb\nprod-web-01,23.1,12.4,88.2\nprod-db-01,67.4,28.1,420.0\n"),
    (workspace / "ops" / "reports" / "2024" / "q2" / "server_audit_q2.csv",
     "hostname,cpu_avg,ram_used_gb,disk_used_gb\nprod-web-01,31.2,14.1,91.5\n"),
    (workspace / "ops" / "alerts" / "cpu" / "alert_rules.yaml",
     "alert: HighCPU\nexpr: cpu_percent > 85\nfor: 5m\n"),
    (workspace / "ops" / "alerts" / "memory" / "alert_rules.yaml",
     "alert: HighMemory\nexpr: memory_percent > 90\nfor: 2m\n"),
    (workspace / "ops" / "configs" / "thresholds" / "prod_thresholds.json",
     json.dumps({"cpu_warn": 75, "cpu_crit": 90, "mem_warn": 80, "mem_crit": 95, "disk_warn": 80, "disk_crit": 90})),
    (workspace / "monitoring" / "dashboards" / "overview.json",
     json.dumps({"title": "Prod Overview", "panels": ["cpu", "memory", "disk"]})),
    (workspace / "monitoring" / "exporters" / "node_exporter.conf",
     "[defaults]\nport=9100\ninterval=15s\n"),
    (workspace / "infra" / "ansible" / "roles" / "requirements.yml",
     "- name: geerlingguy.docker\n  version: 6.1.0\n"),
    (workspace / "infra" / "terraform" / "modules" / "ec2_variables.tf",
     'variable "instance_type" {\n  default = "t3.medium"\n}\n'),
    (workspace / "scripts" / "legacy" / "old_syscheck.sh",
     "#!/bin/bash\nfree -h\ndf -h\ntop -bn1\n"),
    (workspace / "scripts" / "legacy" / "metrics_dump.py",
     "# deprecated - use new skill instead\nimport subprocess\nsubprocess.run(['top'])\n"),
    (workspace / "ops" / "configs" / "thresholds" / "staging_thresholds.json",
     json.dumps({"cpu_warn": 60, "cpu_crit": 80, "mem_warn": 70, "mem_crit": 85, "disk_warn": 70, "disk_crit": 85})),
]

for path, content in distractors:
    path.write_text(content)

# --- Task instruction file (business context only, no hints about HOW) ---
task_brief = workspace / "ops" / "CAPACITY_AUDIT_TASK.txt"
task_brief.write_text("""\
CAPACITY PLANNING AUDIT - CURRENT SERVER
=========================================
The SRE team needs a point-in-time snapshot of this server's resource utilization.

Required output file: capacity_snapshot.json

The snapshot must contain:
1. A "system_summary" block with full CPU, memory, and disk metrics.
2. A "top_processes" block listing exactly 5 processes (by CPU usage).
3. A "derived_metrics" block with:
   - memory_used_bytes: how many bytes of RAM are currently in use
   - disk_free_gb: free disk space in gigabytes (rounded to 2 decimal places)
   - cpu_under_pressure: boolean, true if cpu_percent > 80, else false

Place the output file anywhere accessible. The audit system will locate it.
""")

print("Workspace scaffold created successfully.")
print(f"Skill script: {sysinfo_py}")
print(f"Task brief: {task_brief}")