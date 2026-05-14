import os
import random

random.seed(42)

workspace = "/workspace"

# Create the dados_vps directory structure (as the script would create it)
dados_dir = os.path.join(workspace, "dados_vps")
os.makedirs(dados_dir, exist_ok=True)

# Create the dados_vps file - this is critical, parsed by dados() function
# Format: "Nome do Servidor: X" and "Rede interna: X"
dados_vps_content = """[DADOS DA VPS]

Estes dados foram preenchidos na hora que você foi instalar o Traefik e Portainer e
serão utilizados para realizar as instalações no do SetupOrion v.2

Nome do Servidor: ProdServer01

Rede interna: empresa_net

Email para SSL: devops@empresa-saas.com

Link do Portainer: portainer.empresa-saas.com

Obrigado por utilizar nosso AutoInstalador.
Caso esse conteudo foi util, não deixe de apoiar nosso projeto.

pix@oriondesign.art.br

Bebam água!
"""

with open(os.path.join(dados_dir, "dados_vps"), "w") as f:
    f.write(dados_vps_content)

# Create dados_portainer file - parsed by verificar_arquivo / stack_editavel
dados_portainer_content = """[ PORTAINER ]

Dominio do portainer: portainer.empresa-saas.com

Usuario: admin

Senha: S3nh@Portainer#2024

Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MX0.fakejwttoken123
"""

with open(os.path.join(dados_dir, "dados_portainer"), "w") as f:
    f.write(dados_portainer_content)

# Create dados_postgres - already installed, agent should use this
dados_postgres_content = """[ POSTGRES ]

Dominio do postgres: postgres://postgres:5432

Usuario: postgres

Senha: a3f8b2c91d4e7f6a
"""

with open(os.path.join(dados_dir, "dados_postgres"), "w") as f:
    f.write(dados_postgres_content)

# Create a matching postgres.yaml file (as if postgres was already installed)
postgres_yaml = """version: "3.7"
services:
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_PASSWORD=a3f8b2c91d4e7f6a
      - TZ=America/Sao_Paulo
    networks:
      - empresa_net
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      placement:
        constraints:
          - node.role == manager

volumes:
  postgres_data:
    external: true
    name: postgres_data

networks:
  empresa_net:
    external: true
    name: empresa_net
"""

with open(os.path.join(workspace, "postgres.yaml"), "w") as f:
    f.write(postgres_yaml)

# Create distractors - realistic DevOps files to test contextual awareness
distractor_dirs = [
    "configs/nginx",
    "configs/ssl",
    "deployments/staging",
    "deployments/production/old",
    "scripts/backup",
    "scripts/monitoring",
    "logs/traefik",
    "docs/runbooks",
    "templates/unused",
    "archive/2023",
]

for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "configs/nginx/nginx.conf": "# Nginx config - not used in swarm\nserver { listen 80; }",
    "configs/ssl/letsencrypt.ini": "[certbot]\ndomain = empresa-saas.com\nemail = devops@empresa-saas.com",
    "deployments/staging/docker-compose.yml": "version: '3'\nservices:\n  web:\n    image: nginx:latest",
    "deployments/production/old/n8n-v1.yaml": """# OLD N8N config - do not use
version: "3.7"
services:
  n8n:
    image: n8nio/n8n:0.200.0
    ports:
      - 5678:5678
""",
    "scripts/backup/backup.sh": "#!/bin/bash\n# Backup script\npg_dump -U postgres > /backup/dump.sql",
    "scripts/monitoring/check_health.sh": "#!/bin/bash\ncurl -f http://localhost:5678/healthz || exit 1",
    "logs/traefik/access.log": "2024-01-15 10:23:45 GET /api/v1 200",
    "docs/runbooks/deployment.md": "# Deployment Runbook\n## Steps\n1. Pull latest images\n2. Deploy stack",
    "templates/unused/app.yaml.tmpl": "# Template - not a valid stack file\nSERVICE_NAME: {{.ServiceName}}",
    "archive/2023/old-chatwoot.yaml": "version: '3.7'\nservices:\n  chatwoot:\n    image: chatwoot/chatwoot:v2.0.0",
    "configs/nginx/sites-available.conf": "# Virtual host config\nupstream backend { server 127.0.0.1:3000; }",
    "deployments/production/traefik.yaml": """version: "3.7"
services:
  traefik:
    image: traefik:v3.4.0
    networks:
      - empresa_net
networks:
  empresa_net:
    external: true
    name: empresa_net
""",
    "deployments/production/portainer.yaml": """version: "3.7"
services:
  portainer:
    image: portainer/portainer-ce:latest
    networks:
      - empresa_net
networks:
  empresa_net:
    external: true
    name: empresa_net
""",
}

for filepath, content in distractors.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w") as f:
        f.write(content)

# Create a partially-filled n8n config that is WRONG/incomplete
# to test if agent corrects it vs. uses it as-is
wrong_n8n = """# INCOMPLETE - DO NOT USE AS-IS
version: "3.7"
services:
  n8n:
    image: n8nio/n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_HOST=n8n.empresa-saas.com
"""
with open(os.path.join(workspace, "deployments", "staging", "n8n-draft.yaml"), "w") as f:
    f.write(wrong_n8n)

print("Workspace initialized successfully.")
print(f"Key files created:")
print(f"  - {dados_dir}/dados_vps")
print(f"  - {dados_dir}/dados_portainer")
print(f"  - {dados_dir}/dados_postgres")
print(f"  - {workspace}/postgres.yaml")
print(f"  - {len(distractors)} distractor files")