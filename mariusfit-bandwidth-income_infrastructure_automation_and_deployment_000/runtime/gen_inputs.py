import os
import random
import json

random.seed(42)

BASE = "/workspace"

# --- Create a realistic messy homelab workspace ---

dirs = [
    "homelab/configs",
    "homelab/scripts",
    "homelab/logs",
    "homelab/backups",
    "homelab/nodes/grass",
    "homelab/nodes/mysterium",
    "homelab/nodes/storj",
    "homelab/nodes/honeygain",
    "homelab/monitoring",
    "homelab/earnings",
    "homelab/docs",
    "infra/docker",
    "infra/ansible",
    "infra/terraform",
    "misc/old_configs",
    "misc/drafts",
]

for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)

# --- Distractor files ---

# Old broken compose file (wrong image names, wrong env vars — a trap)
old_compose = """\
version: "3"
services:
  grass:
    image: grass-io/grass-node:v1.2
    container_name: grass
    environment:
      - GRASS_EMAIL=user@example.com
      - GRASS_PASSWORD=secret123
  mysterium:
    image: mysteriumnetwork/mysterium:latest
    container_name: mysterium
    ports:
      - "4449:4449"
  honeygain:
    image: honeygain/node:latest
    container_name: honeygain
    environment:
      - EMAIL=user@example.com
      - PASS=secret123
"""
with open(os.path.join(BASE, "misc/old_configs/docker-compose.old.yml"), "w") as f:
    f.write(old_compose)

# Fake partial monitoring script
bad_monitor = """\
#!/bin/bash
# old monitor script - DO NOT USE
for container in grass mysterium honeygain storj; do
  docker ps | grep $container || echo "$container is down"
done
"""
with open(os.path.join(BASE, "homelab/scripts/old_monitor.sh"), "w") as f:
    f.write(bad_monitor)

# Random log files
logs = [
    ("homelab/logs/grass_2025-01-15.log", "INFO: Connected to grass network\nINFO: Earning 0.0023 GRASS/hr\nERROR: Connection lost\n"),
    ("homelab/logs/mysterium_2025-01-15.log", "node started\nsessions: 3\nbandwidth_used: 1.2GB\n"),
    ("homelab/logs/storj_2025-01-10.log", "disk usage: 234GB/500GB\nearnings_this_month: $12.40\n"),
    ("homelab/logs/monitor_2025-01-14.log", "All nodes running\ngrass-node: OK\nmysterium-node: DOWN - restarted\n"),
]
for path, content in logs:
    with open(os.path.join(BASE, path), "w") as f:
        f.write(content)

# Fake notes file
with open(os.path.join(BASE, "homelab/docs/setup_notes.txt"), "w") as f:
    f.write("""\
Setup notes - Jan 2025
======================
- Tried Grass but wrong image name, kept failing
- Mysterium needs some special docker flag (NET_ADMIN? check docs)
- Storj needs two ports open
- Need to set up proper monitoring with auto-restart
- Honeygain device name should be set to homelab-01
- Earnings at 50Mbps upload seem decent
""")

# Partial earnings draft
with open(os.path.join(BASE, "homelab/earnings/rough_notes.txt"), "w") as f:
    f.write("""\
Bandwidth available: ~50 Mbps upload
Disk available: 500GB

Rough earnings guess (need to verify with official docs):
- Grass: maybe $100?
- Mysterium: no idea
- Storj: $10-50?
- Honeygain: $10-40?
Total: ???

Need proper estimates from official source.
""")

# Fake ansible playbook (distractor)
with open(os.path.join(BASE, "infra/ansible/deploy.yml"), "w") as f:
    f.write("""\
---
- hosts: homelab
  tasks:
    - name: Install docker
      apt:
        name: docker.io
        state: present
""")

# Fake terraform (distractor)
with open(os.path.join(BASE, "infra/terraform/main.tf"), "w") as f:
    f.write("""\
provider "proxmox" {
  pm_api_url = "https://proxmox.local:8006/api2/json"
}
""")

# Old env file with wrong variable names (trap)
with open(os.path.join(BASE, "homelab/configs/old.env"), "w") as f:
    f.write("""\
# OLD - do not use these var names
GRASS_EMAIL=user@example.com
GRASS_PASSWORD=secret
HONEYGAIN_EMAIL=user@example.com
HONEYGAIN_PASSWORD=secret
MYSTERIUM_WALLET=0xDEADBEEF
""")

# Monitoring config stub (incomplete/wrong)
with open(os.path.join(BASE, "homelab/monitoring/monitor_config.json"), "w") as f:
    json.dump({
        "interval_seconds": 60,
        "containers": ["grass", "mysterium", "honeygain"],
        "alert": "email"
    }, f, indent=2)

# Some random scripts
with open(os.path.join(BASE, "homelab/scripts/backup.sh"), "w") as f:
    f.write("#!/bin/bash\ntar czf /backup/homelab_$(date +%Y%m%d).tar.gz /homelab/\n")

with open(os.path.join(BASE, "homelab/scripts/check_disk.sh"), "w") as f:
    f.write("#!/bin/bash\ndf -h /\n")

with open(os.path.join(BASE, "misc/drafts/compose_draft.yml"), "w") as f:
    f.write("""\
# Draft - incomplete
version: "3.8"
services:
  grass:
    image: mrcolorrain/grass:latest
    # TODO: add env vars
""")

# Node-specific distractor configs
with open(os.path.join(BASE, "homelab/nodes/storj/storage.conf"), "w") as f:
    f.write("storage_path=/data/storj\nmax_size=500GB\n# wallet not configured\n")

with open(os.path.join(BASE, "homelab/nodes/mysterium/notes.txt"), "w") as f:
    f.write("Need ERC-20 wallet. Port 4449 must be open. Static IP required.\n")

with open(os.path.join(BASE, "homelab/backups/old_compose_backup.yml"), "w") as f:
    f.write("# empty backup\n")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(BASE):
    for file in files:
        print(f"  {os.path.join(root, file)}")