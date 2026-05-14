import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "openclaw/agents/alpha",
    "openclaw/agents/beta",
    "openclaw/agents/gamma",
    "openclaw/agents/delta",
    "openclaw/agents/epsilon",
    "openclaw/cron",
    "openclaw/gateway",
    "openclaw/logs/alpha",
    "openclaw/logs/beta",
    "openclaw/logs/system",
    "openclaw/config",
    "openclaw/scripts",
    "openclaw/tmp",
    "openclaw/backups",
    "infra/monitoring",
    "infra/systemd",
    "infra/scripts",
    "docs/runbooks",
    "docs/architecture",
]

for d in dirs:
    Path(os.path.join(WORKSPACE, d)).mkdir(parents=True, exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────

# Fake cron job definitions (messy, realistic)
cron_jobs = [
    {"id": "strategy-research", "schedule": "*/5 * * * *", "consecutiveErrors": 0, "enabled": True, "lastRun": "2024-06-01T08:00:00Z"},
    {"id": "portfolio-rebalance", "schedule": "0 */2 * * *", "consecutiveErrors": 2, "enabled": True, "lastRun": "2024-06-01T06:00:00Z"},
    {"id": "risk-monitor", "schedule": "*/15 * * * *", "consecutiveErrors": 0, "enabled": False, "lastRun": "2024-05-31T23:45:00Z"},
    {"id": "data-feed-sync", "schedule": "*/1 * * * *", "consecutiveErrors": 1, "enabled": True, "lastRun": "2024-06-01T07:59:00Z"},
    {"id": "nightly-backup", "schedule": "0 2 * * *", "consecutiveErrors": 0, "enabled": True, "lastRun": "2024-06-01T02:00:00Z"},
]

with open(os.path.join(WORKSPACE, "openclaw/cron/cron-registry.json"), "w") as f:
    json.dump(cron_jobs, f, indent=2)

# Agent process logs (some stale, some fresh)
import time
now = int(time.time())

log_entries = {
    "openclaw/logs/alpha/agent.log": ("2024-06-01 08:01:00 [INFO] alpha: executing strategy scan\n" * 20, now - 5 * 60),       # 5 min ago — fresh
    "openclaw/logs/beta/agent.log": ("2024-06-01 05:30:00 [INFO] beta: idle waiting\n" * 10, now - 180 * 60),                   # 3 hours ago — STALE
    "openclaw/logs/gamma/agent.log": ("2024-06-01 07:55:00 [INFO] gamma: position update\n" * 15, now - 10 * 60),              # 10 min ago — fresh
    "openclaw/logs/system/gateway.log": ("2024-06-01 08:00:00 [INFO] gateway: heartbeat ok\n" * 30, now - 2 * 60),             # 2 min ago
}

for rel_path, (content, mtime) in log_entries.items():
    fpath = os.path.join(WORKSPACE, rel_path)
    with open(fpath, "w") as f:
        f.write(content)
    os.utime(fpath, (mtime, mtime))

# Large log file that needs rotation (>10MB threshold)
large_log_path = os.path.join(WORKSPACE, "openclaw/logs/alpha/strategy-output.log")
with open(large_log_path, "wb") as f:
    f.write(b"2024-06-01 [DATA] market tick: " + b"A" * 100 + b"\n") 
    # Write ~11MB
    chunk = b"2024-06-01 [DATA] market tick: " + b"X" * 200 + b"\n"
    for _ in range(int(11 * 1024 * 1024 / len(chunk)) + 1):
        f.write(chunk)

# Gateway config (distractor)
gateway_config = {
    "host": "localhost",
    "port": 8080,
    "auth": "local",
    "routes": ["alpha", "beta", "gamma"],
    "status": "unknown"
}
with open(os.path.join(WORKSPACE, "openclaw/gateway/gateway-config.json"), "w") as f:
    json.dump(gateway_config, f, indent=2)

# Agent configs (distractors)
for agent in ["alpha", "beta", "gamma", "delta", "epsilon"]:
    cfg = {
        "agentId": agent,
        "strategy": f"{agent}-momentum",
        "riskLimit": random.uniform(0.01, 0.05),
        "logPath": f"/workspace/openclaw/logs/{agent}/agent.log",
        "maxLogAgeMinutes": 30 if agent != "beta" else 15,
    }
    with open(os.path.join(WORKSPACE, f"openclaw/agents/{agent}/config.json"), "w") as f:
        json.dump(cfg, f, indent=2)

# Broken/old systemd attempt (distractor — wrong fields)
broken_service = """[Unit]
Description=Old OpenClaw Monitor

[Service]
ExecStart=/usr/bin/python3 /workspace/old_monitor.py
RestartSec=5
Type=simple

[Install]
WantedBy=multi-user.target
"""
with open(os.path.join(WORKSPACE, "infra/systemd/old-monitor.service"), "w") as f:
    f.write(broken_service)

# An existing incomplete HEARTBEAT draft (wrong thresholds — trap)
bad_heartbeat_draft = """## Health Status

### Crons
- run cron list
- alert if errors > 5
- check disabled jobs

### Processes
- watch beta agent logs
- alert if no update in 60 minutes

### Gateway
- ping gateway

### Disk
- check if logs are too big
"""
with open(os.path.join(WORKSPACE, "docs/runbooks/heartbeat-draft.md"), "w") as f:
    f.write(bad_heartbeat_draft)

# Random architecture notes (distractors)
arch_notes = """# Trading System Architecture

5 competing AI agents run 24/7.
Each agent has dedicated log streams.
Cron jobs coordinate data feeds, risk checks, and backups.
Gateway routes API calls between agents and exchanges.
Monitoring is critical — downtime = missed trades.
"""
with open(os.path.join(WORKSPACE, "docs/architecture/overview.md"), "w") as f:
    f.write(arch_notes)

# Scripts directory — placeholder scripts (distractors)
for s in ["deploy.sh", "rollback.sh", "health-check-old.sh"]:
    with open(os.path.join(WORKSPACE, "openclaw/scripts", s), "w") as f:
        f.write(f"#!/bin/bash\n# {s} placeholder\necho 'Not implemented'\n")

# Temp files (distractors)
for i in range(5):
    with open(os.path.join(WORKSPACE, "openclaw/tmp", f"tmp_data_{i}.bin"), "wb") as f:
        f.write(os.urandom(512))

# A package.json to look like a real Node.js project
pkg = {
    "name": "openclaw-trading-system",
    "version": "2.3.1",
    "description": "Autonomous trading agent cluster",
    "main": "guardian.js",
    "scripts": {
        "start": "node guardian.js",
        "monitor": "node watchdog.js"
    },
    "dependencies": {
        "node-cron": "^3.0.0",
        "axios": "^1.4.0"
    }
}
with open(os.path.join(WORKSPACE, "package.json"), "w") as f:
    json.dump(pkg, f, indent=2)

# Backup log entries
with open(os.path.join(WORKSPACE, "openclaw/backups/backup-log.txt"), "w") as f:
    f.write("2024-06-01 02:00:05 Backup completed. Size: 245MB\n")
    f.write("2024-05-31 02:00:03 Backup completed. Size: 243MB\n")

print("Workspace scaffolded successfully.")