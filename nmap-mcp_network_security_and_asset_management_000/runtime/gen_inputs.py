import os
import json
import random
import yaml
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Clone nmap-mcp ──────────────────────────────────────────────────────────
import subprocess
nmap_mcp_dir = workspace / "nmap-mcp"
if not nmap_mcp_dir.exists():
    result = subprocess.run(
        ["git", "clone", "https://github.com/witchard/nmap-mcp.git", str(nmap_mcp_dir)],
        check=False
    )
    if result.returncode != 0:
        # Clone failed (network issue), create the directory structure manually
        nmap_mcp_dir.mkdir(parents=True, exist_ok=True)
        # Create a minimal server.py so setup.sh doesn't fail
        (nmap_mcp_dir / "server.py").write_text(
            "#!/usr/bin/env python3\n# nmap-mcp server placeholder\n"
        )

# ── Create a BROKEN/INCOMPLETE config.yaml in nmap-mcp ─────────────────────
# Missing allowed_cidrs entirely, scan_dir points to non-existent absolute path,
# audit_log is also wrong. Agent must fix this.
broken_config = {
    # 'allowed_cidrs' is intentionally MISSING — this will cause scope rejection
    "audit_log": "/nonexistent/path/audit.log",   # wrong path
    "scan_dir": "/nonexistent/scans",              # wrong path
    "nmap_bin": "/usr/bin/nmap",
    "timeouts": {
        "quick": 120,
        "standard": 300,
        "deep": 600
    }
}
with open(nmap_mcp_dir / "config.yaml", "w") as f:
    yaml.dump(broken_config, f)

# ── Distractor: a mcporter.json with wrong server path ─────────────────────
mcporter = {
    "nmap": {
        "command": "python3",
        "args": ["-u", "/opt/old-nmap-mcp/server.py"],   # wrong path
        "type": "stdio",
        "env": {
            "NMAP_CONFIG": "/opt/old-nmap-mcp/config.yaml"
        }
    }
}
with open(workspace / "mcporter.json", "w") as f:
    json.dump(mcporter, f, indent=2)

# ── Distractor directory tree (10+ files) ──────────────────────────────────
distractor_dirs = [
    workspace / "infra" / "terraform",
    workspace / "infra" / "ansible" / "roles",
    workspace / "reports" / "2024" / "Q1",
    workspace / "reports" / "2024" / "Q2",
    workspace / "scripts" / "maintenance",
    workspace / "logs" / "old",
    workspace / "compliance" / "pci-dss",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "infra" / "terraform" / "main.tf": "# Terraform placeholder\nresource \"null_resource\" \"example\" {}\n",
    workspace / "infra" / "terraform" / "variables.tf": "variable \"region\" { default = \"us-east-1\" }\n",
    workspace / "infra" / "ansible" / "roles" / "site.yml": "---\n- hosts: all\n  roles: []\n",
    workspace / "infra" / "ansible" / "inventory.ini": "[webservers]\n10.0.0.1\n10.0.0.2\n",
    workspace / "reports" / "2024" / "Q1" / "summary.txt": "Q1 2024 network report - no issues found.\n",
    workspace / "reports" / "2024" / "Q2" / "summary.txt": "Q2 2024 network report - pending review.\n",
    workspace / "scripts" / "maintenance" / "cleanup.sh": "#!/bin/bash\nfind /tmp -mtime +7 -delete\n",
    workspace / "scripts" / "maintenance" / "backup.sh": "#!/bin/bash\nrsync -av /data /backup\n",
    workspace / "logs" / "old" / "syslog.2024-01-01.gz.txt": "compressed log placeholder\n",
    workspace / "logs" / "old" / "auth.log.bak": "Jan  1 00:00:00 host sshd[1234]: Accepted publickey\n",
    workspace / "compliance" / "pci-dss" / "requirements.txt": "PCI DSS v4.0 requirements checklist\n- Req 11.2: Quarterly scans\n",
    workspace / "compliance" / "pci-dss" / "scope.txt": "In-scope: 127.0.0.0/8, 10.0.0.0/8\n",
    workspace / "infra" / "ansible" / "roles" / "nmap_check.yml": "# old ad-hoc nmap check\n# nmap -sT 10.0.0.1 -p 22,80,443\n",
}
for path, content in distractor_files.items():
    path.write_text(content)

# ── Stale/partial scan artifact to confuse the agent ───────────────────────
old_scans_dir = workspace / "old_scans"
old_scans_dir.mkdir(exist_ok=True)
stale_scan = {
    "scan_id": "stale-0000-0000",
    "target": "10.99.99.99",
    "status": "incomplete",
    "note": "this scan was aborted midway"
}
with open(old_scans_dir / "scan_stale.json", "w") as f:
    json.dump(stale_scan, f, indent=2)

# ── A partial/wrong nmap-mcp config in workspace root (distractor) ──────────
wrong_root_config = {
    "allowed_cidrs": ["10.0.0.0/8"],   # correct structure but wrong CIDR (won't cover 127.x)
    "audit_log": "./audit.log",
    "scan_dir": "./scans",
    "nmap_bin": "/usr/bin/nmap"
}
with open(workspace / "config_draft.yaml", "w") as f:
    yaml.dump(wrong_root_config, f)

print("Workspace scaffold complete.")
print(f"nmap-mcp dir: {nmap_mcp_dir}")
print(f"Broken config written to: {nmap_mcp_dir / 'config.yaml'}")