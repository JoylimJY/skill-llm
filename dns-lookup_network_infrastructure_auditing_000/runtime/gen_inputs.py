import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deeply nested distractor directory structure ---
distractor_dirs = [
    "infra/networking/configs",
    "infra/networking/logs",
    "infra/monitoring/alerts",
    "infra/monitoring/dashboards",
    "ops/runbooks/incident",
    "ops/runbooks/maintenance",
    "ops/deployments/prod",
    "ops/deployments/staging",
    "teams/sre/notes",
    "teams/sre/oncall",
    "archive/2023/Q3",
    "archive/2023/Q4",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = [
    ("infra/networking/configs/firewall_rules.txt", "# Firewall rules v2.1\nALLOW tcp 443\nALLOW tcp 80\nDENY ALL\n"),
    ("infra/networking/configs/vlan_map.csv", "vlan_id,subnet,description\n10,192.168.10.0/24,prod\n20,192.168.20.0/24,staging\n"),
    ("infra/networking/logs/network_errors_2024.log", "2024-01-15 03:22:11 ERROR: packet loss on eth0\n2024-01-15 03:22:45 WARN: high latency detected\n"),
    ("infra/monitoring/alerts/pagerduty_config.yaml", "service: my-service\nrouting_key: PLACEHOLDER\nthreshold: 500ms\n"),
    ("infra/monitoring/dashboards/grafana_links.txt", "prod dashboard: http://grafana.internal/d/abc\nstaging: http://grafana.internal/d/def\n"),
    ("ops/runbooks/incident/sev1_playbook.md", "# SEV1 Playbook\n1. Page on-call\n2. Join bridge\n3. Investigate\n"),
    ("ops/runbooks/maintenance/patching_schedule.txt", "Q1: 2024-02-10\nQ2: 2024-05-12\n"),
    ("ops/deployments/prod/deploy_history.log", "2024-03-01 deployed v3.4.1\n2024-03-15 deployed v3.4.2\n"),
    ("ops/deployments/staging/rollback_notes.txt", "Rolled back v3.3.0 due to DB migration failure.\n"),
    ("teams/sre/notes/capacity_planning.txt", "Expected 20% traffic growth in Q3.\nPlan: add 4 nodes to cluster.\n"),
    ("teams/sre/oncall/rotation.csv", "week,engineer\n1,alice\n2,bob\n3,carol\n"),
    ("archive/2023/Q3/old_host_map.txt", "# DEPRECATED - do not use\nweb01: 10.0.1.5\nweb02: 10.0.1.6\n"),
    ("archive/2023/Q4/decommission_list.txt", "legacy-proxy.internal - decommissioned 2023-12-01\nold-db.internal - decommissioned 2023-11-15\n"),
]

for rel_path, content in distractor_files:
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE PROBLEM FILE: messy host manifest ---
# Mix of hostnames and IPs, with blank lines, comments, and extra whitespace
# Uses real, publicly resolvable hostnames and IPs
host_manifest_content = """\
# Host manifest - SRE Infrastructure Audit
# Generated: 2024-06-01 (may be outdated)
# FORMAT: each non-comment line is either a hostname or an IP for reverse lookup
# DO NOT EDIT MANUALLY

  example.com   
# web tier
cloudflare.com

# Known IPs for reverse resolution
8.8.8.8
  1.1.1.1  

# Additional hostnames
google.com
  
# another IP
208.67.222.222

# end of manifest
"""

manifest_path = os.path.join(workspace, "infra/networking/configs/host_manifest.txt")
with open(manifest_path, "w") as f:
    f.write(host_manifest_content)

print("Workspace initialized successfully.")
print(f"Manifest written to: {manifest_path}")