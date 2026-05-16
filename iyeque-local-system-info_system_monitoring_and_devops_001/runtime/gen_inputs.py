import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Create the skill directory and sysinfo.py script ---
skill_dir = workspace / "skills" / "local-system-info"
skill_dir.mkdir(parents=True, exist_ok=True)

sysinfo_script = skill_dir / "sysinfo.py"
sysinfo_script.write_text(r'''#!/usr/bin/env python3
import sys
import json
import psutil
import argparse

def get_cpu():
    load = psutil.getloadavg() if hasattr(psutil, "getloadavg") else [0.0, 0.0, 0.0]
    cpu_count = psutil.cpu_count(logical=True) or 1
    normalized_load = [round(x / cpu_count, 4) for x in load]
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "cpu_count": cpu_count,
        "load_avg": normalized_load
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
                "cpu_percent": round(info["cpu_percent"] or 0.0, 4),
                "memory_percent": round(info["memory_percent"] or 0.0, 4)
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    procs.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return procs[:limit]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["summary", "cpu", "memory", "disk", "processes"])
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.action == "summary":
        result = {"cpu": get_cpu(), "memory": get_memory(), "disk": get_disk()}
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

# --- Create distractor files to test contextual awareness ---

# Distractor: old monitoring configs
config_dir = workspace / "ops" / "monitoring" / "configs"
config_dir.mkdir(parents=True, exist_ok=True)

(config_dir / "legacy_monitor.cfg").write_text("""
[monitor]
interval=30
cpu_threshold=80
mem_threshold=70
disk_threshold=90
alert_email=ops@company.internal
""")

(config_dir / "prometheus.yml").write_text("""
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
""")

# Distractor: deployment scripts
deploy_dir = workspace / "ops" / "deploy"
deploy_dir.mkdir(parents=True, exist_ok=True)

(deploy_dir / "pre_deploy_checklist.txt").write_text("""
Pre-deployment Checklist
========================
1. Verify CPU usage < 70%
2. Verify free memory > 20%
3. Check disk space > 15% free
4. No critical processes crashed in last hour
5. Get sign-off from SRE lead
""")

(deploy_dir / "rollback.sh").write_text("""#!/bin/bash
echo "Rolling back deployment..."
systemctl restart app-service
""")

# Distractor: stale reports directory
reports_dir = workspace / "ops" / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)

(reports_dir / "health_check_2023_11_01.json").write_text(json.dumps({
    "date": "2023-11-01",
    "status": "stale",
    "note": "This is an old report. Do not use."
}, indent=2))

(reports_dir / "health_check_2023_11_15.json").write_text(json.dumps({
    "date": "2023-11-15",
    "cpu_ok": True,
    "memory_ok": False,
    "disk_ok": True
}, indent=2))

# Distractor: app source code
app_dir = workspace / "app" / "src"
app_dir.mkdir(parents=True, exist_ok=True)

(app_dir / "main.py").write_text("""
# Application entry point
def main():
    print("Starting application...")

if __name__ == '__main__':
    main()
""")

(app_dir / "config.py").write_text("""
DATABASE_URL = "postgresql://localhost/proddb"
REDIS_URL = "redis://localhost:6379"
DEBUG = False
""")

# Distractor: logs
logs_dir = workspace / "ops" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

for i in range(3):
    (logs_dir / f"deploy_{i+1}.log").write_text(f"""
2024-01-{i+10:02d} 10:00:00 INFO  Starting deployment #{i+1}
2024-01-{i+10:02d} 10:01:23 INFO  Build successful
2024-01-{i+10:02d} 10:02:45 WARN  High memory usage detected
2024-01-{i+10:02d} 10:04:00 INFO  Deployment complete
""")

# Distractor: README-like but for unrelated tool
(workspace / "ops" / "README_grafana.txt").write_text("""
Grafana Setup
=============
Dashboard URL: http://localhost:3000
Default login: admin/admin
""")

# Distractor: requirements with wrong package name (trap)
(workspace / "requirements_old.txt").write_text("""
psycopg2==2.9.1
flask==2.0.0
gunicorn==20.1.0
# psutil_old -- deprecated, do not use
""")

print("Workspace initialized successfully.")
print(f"Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")