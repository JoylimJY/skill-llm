import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---

dirs = [
    "ops/deploy",
    "ops/monitoring",
    "ops/legacy",
    "infra/network",
    "infra/ssh",
    "infra/backups",
    "scripts/old",
    "scripts/utils",
    "logs/archive",
    "docs/internal",
    "config/staging",
    "config/production",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = [
    ("ops/deploy/deploy_v1.sh", "#!/bin/bash\n# Old deployment script - DO NOT USE\nssh root@10.0.0.1 'systemctl restart app'\n"),
    ("ops/deploy/rollback.sh", "#!/bin/bash\n# Rollback script\ngit checkout HEAD~1\n"),
    ("ops/monitoring/check_disk.sh", "#!/bin/bash\ndf -h | grep -v tmpfs\n"),
    ("ops/monitoring/alert_rules.yaml", "rules:\n  - name: high_cpu\n    threshold: 90\n  - name: low_memory\n    threshold: 10\n"),
    ("ops/legacy/start_old_node.sh", "#!/bin/bash\n# DEPRECATED\nnode server.js --port 3000 &\n"),
    ("infra/network/firewall_rules.txt", "ALLOW 22 FROM 0.0.0.0/0\nALLOW 443 FROM 0.0.0.0/0\nDENY ALL\n"),
    ("infra/ssh/known_hosts_backup.txt", "# Known hosts backup\n192.168.1.1 ssh-rsa AAAAB3Nza...\n"),
    ("infra/backups/backup_2024.tar.gz.manifest", "backup_date: 2024-01-15\nfiles: 3421\nsize: 2.3GB\n"),
    ("scripts/old/node_starter_v0.sh", "#!/bin/bash\n# v0 - broken\ncd /opt/evolver\nnode main.js\n"),
    ("scripts/utils/health_ping.sh", "#!/bin/bash\ncurl -s https://evomap.ai/health | python3 -m json.tool\n"),
    ("logs/archive/evolver_2024_01.log", "[2024-01-01 00:00:01] INFO: Node started\n[2024-01-01 00:01:00] WARN: High latency\n"),
    ("docs/internal/architecture_overview.md", "# Architecture Overview\nEvoMap uses a distributed hub-spoke model.\nNodes communicate via A2A protocol.\nDo not share externally.\n"),
    ("config/staging/env_staging.txt", "# Staging environment - NOT PRODUCTION\nCENTRAL_IP=10.10.0.99\nTOKYO_IP=10.10.0.100\nNODE_ID_DEEP=stg-node-001\n"),
    ("config/production/README_DO_NOT_EDIT.txt", "Contact infra team before making changes to production configs.\n"),
]

for rel_path, content in distractors:
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- MAIN INPUT FILES ---

# cluster_config.ini: messy, realistic config with the actual node IDs and IPs
cluster_config_content = """\
; EvoMap Production Cluster Configuration
; Last updated: 2025-06-10
; Contact: infra@evomap.internal

[general]
environment = production
cluster_name = evomap-prod-cluster
version = 2.4.1

[central_node]
# 深海 node - primary processing unit
display_name = Shenhai Central
node_id = evo-shenhai-prod-7f3a9c
server_ip = 203.0.113.45
region = us-central
status = active
; SSH key for central node
ssh_key_path = ~/.ssh/id_ed25519_central

[tokyo_node]
# 泰拉 node - asia pacific relay
display_name = Tela Tokyo AP
node_id = evo-tela-tokyo-2b8d14
server_ip = 198.51.100.72
region = ap-northeast
status = active
; SSH key for tokyo node
ssh_key_path = ~/.ssh/id_ed25519_tokyo

[silicon_valley_node]
# 天空 node - local silicon valley instance (runs on THIS machine)
display_name = Tiankong SV Local
node_id = evo-tiankong-sv-9a1e05
region = us-west
status = active
; No SSH needed - local execution

[node_runtime]
; Full path for central node only (special NVM install)
central_node_binary = ~/.nvm/versions/node/v22.22.0/bin/node
; Tokyo and SV use system node
default_node_binary = node

[hub]
url = https://evomap.ai
registration_endpoint = /a2a/hello
"""

with open(os.path.join(workspace, "config/production/cluster_config.ini"), "w") as f:
    f.write(cluster_config_content)

# ops_request.txt: the business request / ticket
ops_request_content = """\
OPS TICKET #2025-0847
Priority: HIGH
Requested by: Platform Team Lead

Request:
We need to bring the distributed processing cluster back online after scheduled maintenance.

Specifically:
1. Start the 深海 (central) node and the 泰拉 (Tokyo) node with their respective node identifiers.
2. After starting both, verify the running status of ALL THREE nodes in the cluster
   (including 天空, our local Silicon Valley node).
3. Finally, perform a clean stop of the 泰拉 (Tokyo) node only, as it is being 
   re-provisioned after the health check.

Please generate a shell script called `node_ops.sh` that automates these steps 
in sequence. The script should use the production configuration from 
config/production/cluster_config.ini and be ready for immediate execution 
by the on-call engineer.
"""

with open(os.path.join(workspace, "ops_request.txt"), "w") as f:
    f.write(ops_request_content)

print("Workspace generated successfully.")
print(f"Key files:")
print(f"  - {workspace}/config/production/cluster_config.ini")
print(f"  - {workspace}/ops_request.txt")