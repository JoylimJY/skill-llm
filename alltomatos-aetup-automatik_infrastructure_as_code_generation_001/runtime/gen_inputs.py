import os
import random
import json

random.seed(42)

WORKSPACE = "/workspace"

# Create realistic directory structure for a DevOps/marketing tech company
dirs = [
    "infrastructure/scripts",
    "infrastructure/configs/traefik",
    "infrastructure/configs/portainer",
    "infrastructure/backups",
    "deployment/stacks/production",
    "deployment/stacks/staging",
    "deployment/templates",
    "docs/runbooks",
    "docs/architecture",
    "monitoring/alerts",
    "monitoring/dashboards",
    "assets",
    "references",
    "dados_vps",
]

for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---

# Distractor: An OLD, outdated n8n config (wrong format - docker-compose v2, not swarm)
old_n8n = """version: "2"
services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=localhost
      - DB_TYPE=sqlite
    volumes:
      - n8n_data:/home/node/.n8n
volumes:
  n8n_data:
"""
with open(os.path.join(WORKSPACE, "deployment/stacks/staging/n8n_old.yaml"), "w") as f:
    f.write(old_n8n)

# Distractor: A traefik config (already correct, but for different service)
traefik_config = """version: "3.7"
services:
  traefik:
    image: traefik:v3.4.0
    networks:
      - GrowthNet
    ports:
      - target: 80
        published: 80
        mode: host
      - target: 443
        published: 443
        mode: host
networks:
  GrowthNet:
    external: true
    name: GrowthNet
"""
with open(os.path.join(WORKSPACE, "infrastructure/configs/traefik/traefik.yaml"), "w") as f:
    f.write(traefik_config)

# Distractor: A portainer stack
portainer_yaml = """version: "3.7"
services:
  portainer:
    image: portainer/portainer-ce:latest
    networks:
      - GrowthNet
networks:
  GrowthNet:
    external: true
    name: GrowthNet
"""
with open(os.path.join(WORKSPACE, "infrastructure/configs/portainer/portainer.yaml"), "w") as f:
    f.write(portainer_yaml)

# Distractor: A monitoring config
monitoring_config = {"alert_channels": ["slack", "email"], "check_interval": 60}
with open(os.path.join(WORKSPACE, "monitoring/alerts/config.json"), "w") as f:
    json.dump(monitoring_config, f, indent=2)

# Distractor: A random backup script
with open(os.path.join(WORKSPACE, "infrastructure/backups/backup.sh"), "w") as f:
    f.write("#!/bin/bash\n# Backup script\necho 'Backing up...'\n")

# Distractor: Architecture docs
with open(os.path.join(WORKSPACE, "docs/architecture/overview.md"), "w") as f:
    f.write("# Architecture Overview\n\nOur stack runs on Docker Swarm with Traefik as reverse proxy.\n")

# Distractor: Runbook
with open(os.path.join(WORKSPACE, "docs/runbooks/deployment.md"), "w") as f:
    f.write("# Deployment Runbook\n\nUse the internal installer to deploy services.\n")

# Distractor: Template placeholder
with open(os.path.join(WORKSPACE, "deployment/templates/stack_template.yaml"), "w") as f:
    f.write("# TEMPLATE: Do not use directly\nversion: \"3.7\"\nservices: {}\n")

# Distractor: A Grafana dashboard config
with open(os.path.join(WORKSPACE, "monitoring/dashboards/n8n_metrics.json"), "w") as f:
    json.dump({"title": "N8N Metrics", "panels": []}, f, indent=2)

# Distractor: A wrong postgres config (missing required fields)
wrong_postgres = """version: "3.7"
services:
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_PASSWORD=somepassword
"""
with open(os.path.join(WORKSPACE, "deployment/stacks/staging/postgres_draft.yaml"), "w") as f:
    f.write(wrong_postgres)

# --- KEY INPUT FILES ---

# The SetupOrion.sh script - the agent needs to read this to understand conventions
# We provide a SUBSET of the script focused on the n8n function and its dependencies
# (the full script is referenced in SKILL.md as assets/SetupOrion.sh)
installer_note = """# The full SetupOrion.sh script is available at assets/SetupOrion.sh
# This is the internal installer framework used by the company.
# All stack deployments must follow its exact conventions.
"""
with open(os.path.join(WORKSPACE, "infrastructure/scripts/INSTALLER_NOTE.txt"), "w") as f:
    f.write(installer_note)

# The dados_vps file - server configuration that the installer creates
# The agent must understand this format from reading the script
dados_vps_content = """[DADOS DA VPS]

Estes dados foram preenchidos na hora que você foi instalar o Traefik e Portainer e
serão utilizados para realizar as instalações no do SetupOrion v.2

Nome do Servidor: GrowthTech

Rede interna: GrowthNet

Email para SSL: devops@growthtech.io

Link do Portainer: portainer.growthtech.io

Obrigado por utilizar nosso AutoInstalador.
"""
os.makedirs(os.path.join(WORKSPACE, "dados_vps"), exist_ok=True)
with open(os.path.join(WORKSPACE, "dados_vps/dados_vps"), "w") as f:
    f.write(dados_vps_content)

# The deployment request spec - what parameters the agent needs to use
deployment_spec = {
    "service": "workflow_automation_platform",
    "internal_name": "n8n",
    "instance_suffix": "prod",
    "domains": {
        "editor": "n8n.growthtech.io",
        "webhook": "webhook.growthtech.io"
    },
    "smtp": {
        "sender": "noreply@growthtech.io",
        "user": "noreply@growthtech.io",
        "password": "SmtpP@ss2024",
        "host": "smtp.hostinger.com",
        "port": 465,
        "ssl": True
    },
    "database": {
        "host": "postgres",
        "port": 5432,
        "user": "postgres",
        "password": "Pgr3ssP@ss2024"
    },
    "encryption_key": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6"
}
with open(os.path.join(WORKSPACE, "deployment/n8n_deployment_spec.json"), "w") as f:
    json.dump(deployment_spec, f, indent=2)

# Dados portainer (credentials file the installer needs)
dados_portainer = """[ PORTAINER ]

Dominio do portainer: portainer.growthtech.io

Usuario: admin

Senha: Admin@GrowthTech2024

Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake_token_for_testing
"""
with open(os.path.join(WORKSPACE, "dados_vps/dados_portainer"), "w") as f:
    f.write(dados_portainer)

print("Workspace generated successfully.")
print(f"Key files created:")
print(f"  - {WORKSPACE}/dados_vps/dados_vps")
print(f"  - {WORKSPACE}/deployment/n8n_deployment_spec.json")
print(f"  - {WORKSPACE}/deployment/stacks/staging/n8n_old.yaml (distractor)")