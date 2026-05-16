import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Deep directory structure with distractor files ---
dirs = [
    "compliance/reports/2023",
    "compliance/reports/2024",
    "compliance/evidence",
    "infrastructure/configs/nginx",
    "infrastructure/configs/ssh",
    "infrastructure/inventory/old",
    "infrastructure/inventory/staging",
    "security/audits/Q1",
    "security/audits/Q2",
    "security/tools",
    "logs/access",
    "logs/error",
    "scripts/deprecated",
    "scripts/active",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "compliance/reports/2023/audit_report_2023.txt": "Legacy audit completed. All controls passed.\nNo critical findings.\n",
    "compliance/reports/2024/pending_items.txt": "Items pending:\n- Port inventory for staging\n- Service version documentation\n- Vulnerability pre-scan\n",
    "compliance/evidence/control_matrix.csv": "Control,Status,Owner\nAC-1,Compliant,IT\nSC-7,Pending,SecOps\nRA-5,In Progress,SecOps\n",
    "infrastructure/configs/nginx/nginx.conf.bak": "# Old nginx config backup\nworker_processes 1;\nevents { worker_connections 1024; }\nhttp { server { listen 80; } }\n",
    "infrastructure/configs/ssh/sshd_config.example": "Port 22\nPermitRootLogin no\nPasswordAuthentication yes\n",
    "infrastructure/inventory/old/hosts_2022.txt": "192.168.10.1 gateway\n192.168.10.5 oldserver\n192.168.10.10 db-legacy\n",
    "infrastructure/inventory/staging/notes.txt": "Staging environment target: 127.0.0.1\nServices: web, ssh, custom app\nStatus: UNDOCUMENTED - needs scan\n",
    "security/audits/Q1/findings.json": json.dumps({"quarter": "Q1", "findings": [], "status": "clean"}, indent=2),
    "security/audits/Q2/scope.txt": "Scope for Q2 audit:\n- Staging server (127.0.0.1)\n- Document all open ports\n- Check for known vulnerabilities\n",
    "security/tools/old_scan_attempt.txt": "Attempted manual check on 2024-01-15\nOnly checked port 80 manually\nIncomplete - needs proper tooling\n",
    "logs/access/access.log.1": "127.0.0.1 - - [01/Jan/2024:00:00:01 +0000] \"GET / HTTP/1.1\" 200 612\n",
    "logs/error/error.log.1": "[error] connect() failed (111: Connection refused)\n",
    "scripts/deprecated/manual_check.sh": "#!/bin/bash\n# Old manual port check - DEPRECATED\nfor port in 22 80 443 8080; do\n  nc -z 127.0.0.1 $port && echo \"$port open\" || echo \"$port closed\"\ndone\n",
    "scripts/active/placeholder.txt": "Active scripts directory - automated tooling to be deployed here.\n",
}

for filepath, content in distractors.items():
    full_path = workspace / filepath
    full_path.write_text(content)

# Write a brief mission context file (no hints about HOW to do the work)
mission = workspace / "infrastructure/inventory/staging/mission_context.txt"
mission.write_text(
    "COMPLIANCE TICKET #4471\n"
    "Target: localhost (127.0.0.1)\n"
    "Required deliverables:\n"
    "  1. Full service detection scan output files (all formats)\n"
    "  2. Vulnerability pre-assessment scan output files\n"
    "  3. Machine-readable summary: recon_summary.json\n"
    "Deadline: Before compliance review board meeting.\n"
    "Note: Staging server is running on this local machine.\n"
)

print("Workspace initialized successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")