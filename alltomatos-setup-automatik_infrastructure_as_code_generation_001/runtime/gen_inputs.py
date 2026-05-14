import os
import random

random.seed(42)

workspace = "/workspace"

# --- Create the VPS data directory and config file ---
dados_vps_dir = os.path.join(workspace, "root", "dados_vps")
os.makedirs(dados_vps_dir, exist_ok=True)

dados_vps_content = """[DADOS DA VPS]

Estes dados foram preenchidos na hora que você foi instalar o Traefik e Portainer e
serão utilizados para realizar as instalações no do SetupOrion v.2

Nome do Servidor: AgenciaAutomatik

Rede interna: AutomatikNet

Email para SSL: devops@automatik.com.br

Link do Portainer: portainer.automatik.com.br

Obrigado por utilizar nosso AutoInstalador.
Caso esse conteudo foi util, não deixe de apoiar nosso projeto.

pix@oriondesign.art.br

Bebam água!
"""

with open(os.path.join(dados_vps_dir, "dados_vps"), "w") as f:
    f.write(dados_vps_content)

# --- Create an existing postgres.yaml (simulating prior postgres install) ---
# The agent must read this to get the password, mirroring pegar_senha_postgres()
postgres_password = "a3f8c12b9e4d7f2a"

postgres_yaml_content = f"""version: "3.7"
services:

## --------------------------- ORION --------------------------- ##

  postgres:
    image: postgres:14 ## Versão do postgres
    command: >
      postgres
      -c max_connections=500
      -c shared_buffers=512MB
      -c timezone=America/Sao_Paulo

    volumes:
      - postgres_data:/var/lib/postgresql/data

    networks:
      - AutomatikNet ## Nome da rede interna

    environment:
      ## 🔑 Senha do Postgres 
      - POSTGRES_PASSWORD={postgres_password}

      ## 🌎 Timezone
      - TZ=America/Sao_Paulo

    deploy:
      mode: replicated
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      resources:
        limits:
          cpus: "1"
          memory: 1024M

## --------------------------- ORION --------------------------- ##

volumes:
  postgres_data:
    external: true
    name: postgres_data

networks:
  AutomatikNet: ## Nome da rede interna
    external: true
    name: AutomatikNet ## Nome da rede interna
"""

with open(os.path.join(workspace, "root", "postgres.yaml"), "w") as f:
    f.write(postgres_yaml_content)

# --- Distractor files to simulate a real VPS environment ---
distractor_dirs = [
    os.path.join(workspace, "root", "dados_vps"),
    os.path.join(workspace, "root", "logs"),
    os.path.join(workspace, "etc", "traefik"),
    os.path.join(workspace, "var", "lib", "docker", "volumes"),
    os.path.join(workspace, "root", "backups"),
    os.path.join(workspace, "opt", "stacks"),
    os.path.join(workspace, "tmp", "deploy"),
]

for d in distractor_dirs:
    os.makedirs(d, exist_ok=True)

# Distractor file 1: old portainer data
with open(os.path.join(workspace, "root", "dados_vps", "dados_portainer"), "w") as f:
    f.write("[ PORTAINER ]\n\nDominio do portainer: portainer.automatik.com.br\n\nUsuario: admin\n\nSenha: AdminPass@2024\n\nToken: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.fake\n")

# Distractor file 2: old evolution config
with open(os.path.join(workspace, "root", "evolution.yaml"), "w") as f:
    f.write("version: '3.7'\nservices:\n  evolution:\n    image: evoapicloud/evolution-api:latest\n    environment:\n      - SERVER_URL=https://api.automatik.com.br\n      - AUTHENTICATION_API_KEY=old_api_key_12345\n")

# Distractor file 3: traefik config
with open(os.path.join(workspace, "etc", "traefik", "traefik.yml"), "w") as f:
    f.write("entryPoints:\n  web:\n    address: ':80'\n  websecure:\n    address: ':443'\n")

# Distractor file 4: a random log file
with open(os.path.join(workspace, "root", "logs", "deploy.log"), "w") as f:
    f.write("[2024-01-15 10:23:11] Deploy started\n[2024-01-15 10:23:45] Stack traefik deployed\n[2024-01-15 10:25:00] Stack portainer deployed\n")

# Distractor file 5: old n8n config (wrong format, should not be used)
with open(os.path.join(workspace, "root", "n8n_old.yaml"), "w") as f:
    f.write("version: '3'\nservices:\n  n8n:\n    image: n8nio/n8n\n    ports:\n      - '5678:5678'\n    environment:\n      - DB_TYPE=sqlite\n")

# Distractor file 6: random backup
with open(os.path.join(workspace, "root", "backups", "stack_backup_20240101.tar.gz.txt"), "w") as f:
    f.write("backup placeholder\n")

# Distractor file 7: minio config
with open(os.path.join(workspace, "root", "minio.yaml"), "w") as f:
    f.write("version: '3.7'\nservices:\n  minio:\n    image: quay.io/minio/minio:latest\n    environment:\n      - MINIO_ROOT_USER=minioadmin\n      - MINIO_ROOT_PASSWORD=minio_secret_pw\n      - MINIO_BROWSER_REDIRECT_URL=https://minio.automatik.com.br\n      - MINIO_SERVER_URL=https://s3.automatik.com.br\n")

# Distractor file 8: chatwoot data
with open(os.path.join(workspace, "root", "dados_vps", "dados_chatwoot"), "w") as f:
    f.write("[ CHATWOOT ]\n\nDominio do Chatwoot: https://chat.automatik.com.br\n\nUsuario: admin@automatik.com.br\n\nSenha: ChatPass@2024\n")

# Distractor file 9: docker compose generic (wrong format)
with open(os.path.join(workspace, "opt", "stacks", "generic-compose.yml"), "w") as f:
    f.write("version: '3'\nservices:\n  app:\n    image: myapp:latest\n    ports:\n      - '8080:8080'\n")

# Distractor file 10: redis standalone config
with open(os.path.join(workspace, "root", "redis_standalone.yaml"), "w") as f:
    f.write("version: '3.7'\nservices:\n  redis:\n    image: redis:latest\n    command: redis-server --appendonly yes --port 6379\n    volumes:\n      - redis_data:/data\n")

print("Workspace generated successfully.")
print(f"Postgres password set to: {postgres_password}")
print("Agent must create: n8n_cliente1.yaml in /workspace/root/")