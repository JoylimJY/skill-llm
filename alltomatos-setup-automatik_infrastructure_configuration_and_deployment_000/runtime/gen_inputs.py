import os
import random
import json

random.seed(42)

workspace = "/workspace"

# Create realistic nested directory structure with distractor files
dirs = [
    "assets",
    "references",
    "server-configs",
    "server-configs/staging",
    "server-configs/production",
    "server-configs/backups",
    "logs",
    "logs/traefik",
    "logs/portainer",
    "monitoring",
    "scripts",
    "credentials",
    "dados_vps",  # This is where Orion stores data, but we intentionally leave it INCOMPLETE
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files to simulate a realistic messy workspace
distractor_files = {
    "server-configs/staging/docker-compose.yml": """version: "3"
services:
  app:
    image: myapp:latest
""",
    "server-configs/production/notes.txt": "Production server: 10.0.0.5\nContact: devops@company.com\n",
    "server-configs/backups/backup_20240101.tar.gz.info": "Backup taken on 2024-01-01 at 03:00 UTC\n",
    "logs/traefik/access.log": "10.0.0.1 - - [01/Jan/2024] GET / HTTP/1.1 200\n",
    "logs/portainer/errors.log": "ERR: Container not found\n",
    "monitoring/alerts.json": json.dumps({"alerts": [], "last_check": "2024-01-01T00:00:00Z"}),
    "scripts/cleanup.sh": "#!/bin/bash\ndocker system prune -f\n",
    "scripts/backup.sh": "#!/bin/bash\ntar -czf backup.tar.gz /data\n",
    "credentials/README_DELETE_ME.txt": "Old credentials file - no longer valid\n",
    "assets/SetupOrion.sh": "# Placeholder - actual script is managed separately\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# Create a PARTIAL/INCOMPLETE dados_vps file - the agent must understand the correct format
# and create the proper files. This one is intentionally malformed/incomplete.
incomplete_dados = """[DADOS DA VPS]

Nome do Servidor = MyProductionServer
rede_interna = OrionNetwork
email = admin@example.com
portainer_url = portainer.example.com
"""
with open(os.path.join(workspace, "dados_vps", "dados_vps_draft.txt"), "w") as f:
    f.write(incomplete_dados)

# Create a reference file with the deployment parameters the agent needs to use
deployment_params = {
    "server_name": "ProdServerAlpha",
    "internal_network": "AlphaNet",
    "ssl_email": "ops@alphacompany.io",
    "portainer_domain": "portainer.alphacompany.io",
    "portainer_user": "alpha_admin",
    "portainer_password": "SecurePass2024@",
    "portainer_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock_token_value",
    "uptime_kuma_domain": "uptime.alphacompany.io",
    "stack_name": "uptimekuma"
}

with open(os.path.join(workspace, "deployment_params.json"), "w") as f:
    json.dump(deployment_params, f, indent=2)

# Create references/tools.md as a distractor (same as skill)
tools_ref = """# Available Tools Reference
- Uptime Kuma: monitoring tool
- Traefik: reverse proxy
- Portainer: container management
"""
with open(os.path.join(workspace, "references", "tools.md"), "w") as f:
    f.write(tools_ref)

print("Workspace generated successfully.")
print(f"Files created in {workspace}")