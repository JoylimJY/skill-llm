import os
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "devops/reports/2024",
    "devops/reports/2025",
    "devops/configs/nginx",
    "devops/configs/systemd",
    "devops/scripts/deploy",
    "devops/scripts/monitor",
    "devops/logs/archived",
    "docs/handover",
    "docs/runbooks",
    "tools/diagnostics",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files — realistic but irrelevant
distractor_files = {
    "devops/configs/nginx/nginx.conf": """worker_processes auto;
events { worker_connections 1024; }
http {
    server {
        listen 80;
        server_name example.com;
        location / { proxy_pass http://localhost:8080; }
    }
}
""",
    "devops/configs/systemd/app-gateway.service": """[Unit]
Description=App Gateway Service
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/node /opt/app/dist/index.js gateway
Restart=on-failure

[Install]
WantedBy=default.target
""",
    "devops/scripts/deploy/rollback.sh": """#!/bin/bash
set -e
echo "Rolling back to previous version..."
systemctl --user stop app-gateway.service
cp /opt/app/backup/* /opt/app/dist/
systemctl --user start app-gateway.service
echo "Rollback complete"
""",
    "devops/scripts/monitor/check_ports.sh": """#!/bin/bash
netstat -tlnp | grep -E ':(8080|9090|19922)' || echo "No services listening"
""",
    "devops/logs/archived/app-2024-12-01.log": "\n".join(
        [f"2024-12-01 {random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d} INFO Service running normally" for _ in range(80)]
    ),
    "devops/reports/2024/health-check-dec.txt": """Health Check Report - December 2024
All services nominal.
CPU: 23%
Memory: 45%
""",
    "devops/reports/2025/template.txt": """Health Check Report Template
============================
Date:
Services Checked:
Issues Found:
Resolution:
""",
    "docs/runbooks/gateway-restart.md": """# Gateway Restart Runbook
1. Check current status
2. Stop service
3. Clear temp files
4. Start service
5. Verify
""",
    "docs/handover/previous-report-2025-03.txt": """Handover Notes - March 2025
Previous engineer completed gateway migration.
No outstanding issues at time of handover.
""",
    "tools/diagnostics/port-scanner.py": """#!/usr/bin/env python3
import socket
ports = [8080, 9090, 19922, 3000]
for port in ports:
    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect(('127.0.0.1', port))
        print(f'Port {port}: OPEN')
        s.close()
    except:
        print(f'Port {port}: CLOSED')
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# The KEY input: a raw "notes" file describing the session the agent must document
# This is messy, unstructured — the agent must turn it into a properly formatted report
session_notes_content = """=== SYSTEM DIAGNOSTIC SESSION NOTES ===
Engineer: Li Wei
Date: 2025-06-15
Purpose: Pre-deployment health check for gateway cluster

--- STEP 1: Check disk space ---
Ran: df -h /opt
Got back:
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   31G   17G  65% /opt
Looked fine.

--- STEP 2: Check running services ---
Ran: systemctl --user list-units --type=service --state=running --no-pager
Got back:
  UNIT                          LOAD   ACTIVE SUB     DESCRIPTION
  app-gateway-main.service      loaded active running App Gateway Main
  app-gateway-boss.service      loaded active running App Gateway Boss
  redis.service                 loaded active running Redis In-Memory Data Store
  postgres.service              loaded active running PostgreSQL RDBMS

LOAD = Reflects whether the unit definition was properly loaded.
ACTIVE = The high-level unit activation state.
SUB = The low-level unit activation state.

4 loaded units listed.
All good.

--- STEP 3: Inspect gateway log (long output) ---
Ran: journalctl --user -u app-gateway-main.service --no-pager
The output had 127 lines total. Here are the first few:
Jun 15 09:01:03 prod-server node[4521]: info: Gateway starting on port 19922
Jun 15 09:01:04 prod-server node[4521]: info: Connected to Redis
Jun 15 09:01:04 prod-server node[4521]: info: Connected to PostgreSQL
Jun 15 09:01:05 prod-server node[4521]: info: Loaded 42 channel configurations
Jun 15 09:01:05 prod-server node[4521]: info: Gateway ready
Jun 15 09:01:10 prod-server node[4521]: info: First connection accepted from 10.0.0.5
Jun 15 09:05:22 prod-server node[4521]: warn: Slow query detected (245ms) on /api/sessions
Jun 15 09:11:47 prod-server node[4521]: info: Health check passed
Jun 15 09:15:33 prod-server node[4521]: info: 128 active sessions
Jun 15 09:22:01 prod-server node[4521]: info: Configuration reload triggered
Jun 15 09:22:02 prod-server node[4521]: info: Reload complete, 42 channels active
Jun 15 09:30:00 prod-server node[4521]: info: Health check passed
Jun 15 09:45:00 prod-server node[4521]: info: Health check passed
Jun 15 10:00:00 prod-server node[4521]: info: Health check passed
Jun 15 10:01:03 prod-server node[4521]: info: 97 active sessions
Jun 15 10:15:00 prod-server node[4521]: info: Health check passed
Jun 15 10:30:00 prod-server node[4521]: info: Health check passed
Jun 15 10:45:00 prod-server node[4521]: info: Health check passed
Jun 15 11:00:00 prod-server node[4521]: info: Health check passed
Jun 15 11:01:03 prod-server node[4521]: info: 115 active sessions
Jun 15 11:15:00 prod-server node[4521]: info: Health check passed
Jun 15 11:30:00 prod-server node[4521]: info: Health check passed
Jun 15 11:45:00 prod-server node[4521]: info: Health check passed
Jun 15 12:00:00 prod-server node[4521]: info: Health check passed
Jun 15 12:01:03 prod-server node[4521]: info: 131 active sessions
Jun 15 12:15:00 prod-server node[4521]: info: Health check passed
Jun 15 12:30:00 prod-server node[4521]: info: Health check passed
Jun 15 12:45:00 prod-server node[4521]: info: Health check passed
Jun 15 13:00:00 prod-server node[4521]: info: Health check passed
Jun 15 13:01:03 prod-server node[4521]: info: 108 active sessions
Jun 15 13:15:00 prod-server node[4521]: info: Health check passed
Jun 15 13:30:00 prod-server node[4521]: info: Health check passed
Jun 15 13:45:00 prod-server node[4521]: info: Health check passed
Jun 15 14:00:00 prod-server node[4521]: info: Health check passed
Jun 15 14:01:03 prod-server node[4521]: info: 119 active sessions
Jun 15 14:15:00 prod-server node[4521]: info: Health check passed
Jun 15 14:30:00 prod-server node[4521]: info: Health check passed
Jun 15 14:45:00 prod-server node[4521]: info: Health check passed
Jun 15 15:00:00 prod-server node[4521]: info: Health check passed
Jun 15 15:01:03 prod-server node[4521]: info: 122 active sessions
Jun 15 15:15:00 prod-server node[4521]: info: Health check passed
Jun 15 15:30:00 prod-server node[4521]: info: Health check passed
Jun 15 15:45:00 prod-server node[4521]: info: Health check passed
Jun 15 16:00:00 prod-server node[4521]: info: Health check passed
Jun 15 16:01:03 prod-server node[4521]: info: 134 active sessions
Jun 15 16:15:00 prod-server node[4521]: info: Health check passed
Jun 15 16:30:00 prod-server node[4521]: info: Health check passed
[... more health check lines ...]
Interpretation: Gateway has been stable all day. Slow query at 09:05 is known issue, ticket #4821 open.

--- STEP 4: Attempted config reload via API ---
Ran: curl -X POST http://localhost:19922/admin/reload --header "Content-Type: application/json" --data '{"force": true}'
FAILED. Got error:
curl: (7) Failed to connect to localhost port 19922 after 0 ms: Connection refused
Exit code was 7.
Reason: Admin endpoint not exposed on main gateway in this environment. Use internal management port 19923 instead.

--- STEP 5: Verify directory structure ---
Ran: tree -L 3 /opt/app/dist/
Got:
/opt/app/dist/
├── index.js
├── gateway
│   ├── index.js
│   ├── router.js
│   └── middleware.js
├── channels
│   ├── whatsapp.js
│   ├── telegram.js
│   └── discord.js
└── utils
    ├── logger.js
    ├── config.js
    └── redis.js

3 directories, 10 files
Structure looks correct.

=== END OF SESSION NOTES ===
"""

with open(os.path.join(workspace, "devops/reports/2025/session_notes_2025-06-15.txt"), "w") as f:
    f.write(session_notes_content)

print("Workspace generated successfully.")
print(f"Key input file: {workspace}/devops/reports/2025/session_notes_2025-06-15.txt")