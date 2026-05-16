import os
import random
import json

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create a realistic, deeply nested directory structure with distractor files
# Simulating a DevOps/Infrastructure repository

dirs = [
    "assets",
    "references",
    "deployments/staging",
    "deployments/production",
    "deployments/testing",
    "configs/traefik",
    "configs/nginx",
    "configs/databases",
    "scripts/maintenance",
    "scripts/backup",
    "docs/architecture",
    "docs/runbooks",
    "monitoring/grafana/dashboards",
    "monitoring/prometheus",
    "secrets/staging",
    "secrets/production",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# The actual SetupOrion.sh script (simplified but with the N8N section intact)
# We provide the full script as it exists in assets/
setup_script_content = r"""#!/bin/bash

## ORION DESIGN SetupOrion v.2.7.1

amarelo="\e[33m"
verde="\e[32m"
branco="\e[97m"
bege="\e[93m"
vermelho="\e[91m"
reset="\e[0m"

home_directory="$HOME"
dados_vps="${home_directory}/dados_vps/dados_vps"

dados() {
    nome_servidor=$(grep "Nome do Servidor:" "$dados_vps" | awk -F': ' '{print $2}')
    nome_rede_interna=$(grep "Rede interna:" "$dados_vps" | awk -F': ' '{print $2}')
}

ferramenta_n8n() {

## Verifica os recursos
recursos 2 2 && continue || return

## Limpa o terminal
clear

## Ativa a função dados para pegar os dados da vps
dados

## Mostra o nome da aplicação
nome_n8n

## Mostra mensagem para preencher informações
preencha_as_info

## Inicia um Loop até os dados estarem certos
while true; do

    ##Pergunta o Dominio do N8N
    echo -e "\e[97mPasso$amarelo 1/7\e[0m"
    echo -en "\e[33mDigite o dominio para o N8N (ex: n8n.oriondesign.art.br): \e[0m" && read -r url_editorn8n
    echo ""
    
    ##Pergunta o Dominio do Webhook
    echo -e "\e[97mPasso$amarelo 2/7\e[0m"
    echo -en "\e[33mDigite o dominio para o Webhook do N8N (ex: webhook.oriondesign.art.br): \e[0m" && read -r url_webhookn8n
    echo ""

    ##Pergunta o Email SMTP
    echo -e "\e[97mPasso$amarelo 3/7\e[0m"
    echo -en "\e[33mDigite o Email para SMTP (ex: contato@oriondesign.art.br): \e[0m" && read -r email_smtp_n8n
    echo ""

    ##Pergunta o usuário do Email SMTP
    echo -e "\e[97mPasso$amarelo 4/7\e[0m"
    echo -e "$amarelo--> Caso não tiver um usuario do email, use o proprio email abaixo"
    echo -en "\e[33mDigite o Usuário para SMTP (ex: oriondesign ou contato@oriondesign.art.br): \e[0m" && read -r usuario_smtp_n8n
    echo ""
    
    ## Pergunta a senha do SMTP
    echo -e "\e[97mPasso$amarelo 5/7\e[0m"
    echo -e "$amarelo--> Sem caracteres especiais: \!#$ | Se estiver usando gmail use a senha de app"
    echo -en "\e[33mDigite a Senha SMTP do Email (ex: @Senha123_): \e[0m" && read -r senha_smtp_n8n
    echo ""

    ## Pergunta o Host SMTP do email
    echo -e "\e[97mPasso$amarelo 6/7\e[0m"
    echo -en "\e[33mDigite o Host SMTP do Email (ex: smtp.hostinger.com): \e[0m" && read -r host_smtp_n8n
    echo ""

    ## Pergunta a porta SMTP do email
    echo -e "\e[97mPasso$amarelo 7/7\e[0m"
    echo -en "\e[33mDigite a porta SMTP do Email (ex: 465): \e[0m" && read -r porta_smtp_n8n
    echo ""

    ## Verifica se a porta é 465, se sim deixa o ssl true, se não, deixa false 
    if [ "$porta_smtp_typebot" -eq 465 ]; then
    smtp_secure_smtp_n8n=true
    else
    smtp_secure_smtp_n8n=false
    fi
        
done

## Mensagem de Passo
echo -e "\e[97m• INICIANDO A INSTALAÇÃO DO N8N \e[33m[1/4]\e[0m"
echo ""

## Verifica se tem postgres, se sim pega a senha e cria um banco nele, se não instala, pega a senha e cria o banco
verificar_container_postgres
if [ $? -eq 0 ]; then
    echo "1/3 - [ OK ] - Postgres já instalado"
    pegar_senha_postgres > /dev/null 2>&1
    echo "2/3 - [ OK ] - Copiando senha do Postgres"
    criar_banco_postgres_da_stack "n8n_queue${1:+_$1}"
    echo "3/3 - [ OK ] - Criando banco de dados"
    echo ""
else
    ferramenta_postgres
    pegar_senha_postgres > /dev/null 2>&1
    criar_banco_postgres_da_stack "n8n_queue${1:+_$1}"
fi

## Criando key Aleatória
encryption_key=$(openssl rand -hex 16)

## Criando a stack n8n.yaml
cat > n8n${1:+_$1}.yaml <<EOL
version: "3.7"
services:

## --------------------------- ORION --------------------------- ##

  n8n${1:+_$1}_editor:
    image: n8nio/n8n:latest ## Versão do N8N
    command: start

    networks:
      - $nome_rede_interna ## Nome da rede interna

    environment:
    ## 🗄️ Banco de Dados (PostgreSQL)
      - N8N_FIX_MIGRATIONS=true 
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_DATABASE=n8n_queue${1:+_$1}
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=$senha_postgres

    ## 🔐 Criptografia
      - N8N_ENCRYPTION_KEY=$encryption_key

    ## 🌐 URLs e Configurações de Acesso
      - N8N_HOST=$url_editorn8n
      - N8N_EDITOR_BASE_URL=https://$url_editorn8n/
      - WEBHOOK_URL=https://$url_webhookn8n/
      - N8N_PROTOCOL=https
      - N8N_ONBOARDING_FLOW_DISABLED=true

    ## ⚙️ Ambiente de Execução
      - NODE_ENV=production
      - EXECUTIONS_MODE=queue
      - EXECUTIONS_TIMEOUT=3600
      - EXECUTIONS_TIMEOUT_MAX=7200
      - OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true
      - N8N_RUNNERS_ENABLED=true
      - N8N_RUNNERS_MODE=internal
      - N8N_RUNNERS_MAX_CONCURRENCY=5

    ## 📦 Pacotes e Nós Comunitários
      - N8N_REINSTALL_MISSING_PACKAGES=true
      - N8N_COMMUNITY_PACKAGES_ENABLED=true
      - N8N_NODE_PATH=/home/node/.n8n/nodes
      - N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true

    ## 📧 SMTP (Envio de E-mails)
      - N8N_SMTP_SENDER=$email_smtp_n8n
      - N8N_SMTP_USER=$usuario_smtp_n8n
      - N8N_SMTP_PASS=$senha_smtp_n8n
      - N8N_SMTP_HOST=$host_smtp_n8n
      - N8N_SMTP_PORT=$porta_smtp_n8n
      - N8N_SMTP_SSL=$smtp_secure_smtp_n8n

    ## 🔁 Redis (Fila de Execução)
      - QUEUE_BULL_REDIS_HOST=n8n${1:+_$1}_redis
      - QUEUE_BULL_REDIS_PORT=6379
      - QUEUE_BULL_REDIS_DB=1

    ## 📊 Métricas
      - N8N_METRICS=true

    ## ⏱️ Execuções e Limpeza
      - EXECUTIONS_DATA_PRUNE=true
      - EXECUTIONS_DATA_MAX_AGE=336

    ## 🧠 Recursos de IA
      - N8N_AI_ENABLED=false
      - N8N_AI_PROVIDER=openai
      - N8N_AI_OPENAI_API_KEY=

    ## 🧰 Permissões em Funções Personalizadas
      - NODE_FUNCTION_ALLOW_BUILTIN=*
      - NODE_FUNCTION_ALLOW_EXTERNAL=moment,lodash

    ## 🕒 Fuso Horário
      - GENERIC_TIMEZONE=America/Sao_Paulo
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
      labels:
        - traefik.enable=true
        - traefik.http.routers.n8n${1:+_$1}_editor.rule=Host(\`$url_editorn8n\`) ## Url do Editor do N8N
        - traefik.http.routers.n8n${1:+_$1}_editor.entrypoints=websecure
        - traefik.http.routers.n8n${1:+_$1}_editor.priority=1
        - traefik.http.routers.n8n${1:+_$1}_editor.tls.certresolver=letsencryptresolver
        - traefik.http.routers.n8n${1:+_$1}_editor.service=n8n${1:+_$1}_editor
        - traefik.http.services.n8n${1:+_$1}_editor.loadbalancer.server.port=5678
        - traefik.http.services.n8n${1:+_$1}_editor.loadbalancer.passHostHeader=1

## --------------------------- ORION --------------------------- ##

  n8n${1:+_$1}_webhook:
    image: n8nio/n8n:latest ## Versão do N8N
    command: webhook

    networks:
      - $nome_rede_interna ## Nome da rede interna

    environment:
      ## 🗄️ Banco de Dados (PostgreSQL)
      - N8N_FIX_MIGRATIONS=true 
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_DATABASE=n8n_queue${1:+_$1}
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=$senha_postgres

      ## 🔐 Criptografia
      - N8N_ENCRYPTION_KEY=$encryption_key

      ## 🌐 URLs e Configurações de Acesso
      - N8N_HOST=$url_editorn8n
      - N8N_EDITOR_BASE_URL=https://$url_editorn8n/
      - WEBHOOK_URL=https://$url_webhookn8n/
      - N8N_PROTOCOL=https
      - N8N_ONBOARDING_FLOW_DISABLED=true

      ## ⚙️ Ambiente de Execução
      - NODE_ENV=production
      - EXECUTIONS_MODE=queue
      - EXECUTIONS_TIMEOUT=3600
      - EXECUTIONS_TIMEOUT_MAX=7200
      - OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true
      - N8N_RUNNERS_ENABLED=true
      - N8N_RUNNERS_MODE=internal

      ## 📦 Pacotes e Nós Comunitários
      - N8N_REINSTALL_MISSING_PACKAGES=true
      - N8N_COMMUNITY_PACKAGES_ENABLED=true
      - N8N_NODE_PATH=/home/node/.n8n/nodes
      - N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true

      ## 📧 SMTP (Envio de E-mails)
      - N8N_SMTP_SENDER=$email_smtp_n8n
      - N8N_SMTP_USER=$usuario_smtp_n8n
      - N8N_SMTP_PASS=$senha_smtp_n8n
      - N8N_SMTP_HOST=$host_smtp_n8n
      - N8N_SMTP_PORT=$porta_smtp_n8n
      - N8N_SMTP_SSL=$smtp_secure_smtp_n8n

      ## 🔁 Redis (Fila de Execução)
      - QUEUE_BULL_REDIS_HOST=n8n${1:+_$1}_redis
      - QUEUE_BULL_REDIS_PORT=6379
      - QUEUE_BULL_REDIS_DB=1

      ## 📊 Métricas
      - N8N_METRICS=true

      ## ⏱️ Execuções e Limpeza
      - EXECUTIONS_DATA_PRUNE=true
      - EXECUTIONS_DATA_MAX_AGE=336

      ## 🧠 Recursos de IA
      - N8N_AI_ENABLED=false
      - N8N_AI_PROVIDER=openai
      - N8N_AI_OPENAI_API_KEY=

      ## 🧰 Permissões em Funções Personalizadas
      - NODE_FUNCTION_ALLOW_BUILTIN=*
      - NODE_FUNCTION_ALLOW_EXTERNAL=moment,lodash

      ## 🕒 Fuso Horário
      - GENERIC_TIMEZONE=America/Sao_Paulo
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
      labels:
        - traefik.enable=true
        - traefik.http.routers.n8n${1:+_$1}_webhook.rule=(Host(\`$url_webhookn8n\`) && PathPrefix(\`/webhook\`)) ## Url do Webhook do N8N
        - traefik.http.routers.n8n${1:+_$1}_webhook.entrypoints=websecure
        - traefik.http.routers.n8n${1:+_$1}_webhook.priority=1
        - traefik.http.routers.n8n${1:+_$1}_webhook.tls.certresolver=letsencryptresolver
        - traefik.http.routers.n8n${1:+_$1}_webhook.service=n8n${1:+_$1}_webhook
        - traefik.http.services.n8n${1:+_$1}_webhook.loadbalancer.server.port=5678
        - traefik.http.services.n8n${1:+_$1}_webhook.loadbalancer.passHostHeader=1

## --------------------------- ORION --------------------------- ##

  n8n${1:+_$1}_worker:
    image: n8nio/n8n:latest ## Versão do N8N
    command: worker --concurrency=10

    networks:
      - $nome_rede_interna ## Nome da rede interna

    environment:
      ## 🗄️ Banco de Dados (PostgreSQL)
      - N8N_FIX_MIGRATIONS=true 
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_DATABASE=n8n_queue${1:+_$1}
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=$senha_postgres

      ## 🔐 Criptografia
      - N8N_ENCRYPTION_KEY=$encryption_key

      ## 🌐 URLs e Configurações de Acesso
      - N8N_HOST=$url_editorn8n
      - N8N_EDITOR_BASE_URL=https://$url_editorn8n/
      - WEBHOOK_URL=https://$url_webhookn8n/
      - N8N_PROTOCOL=https
      - N8N_ONBOARDING_FLOW_DISABLED=true

      ## ⚙️ Ambiente de Execução
      - NODE_ENV=production
      - EXECUTIONS_MODE=queue
      - EXECUTIONS_TIMEOUT=3600
      - EXECUTIONS_TIMEOUT_MAX=7200
      - OFFLOAD_MANUAL_EXECUTIONS_TO_WORKERS=true
      - N8N_RUNNERS_ENABLED=true
      - N8N_RUNNERS_MODE=internal

      ## 📦 Pacotes e Nós Comunitários
      - N8N_REINSTALL_MISSING_PACKAGES=true
      - N8N_COMMUNITY_PACKAGES_ENABLED=true
      - N8N_NODE_PATH=/home/node/.n8n/nodes
      - N8N_ENFORCE_SETTINGS_FILE_PERMISSIONS=true

      ## 📧 SMTP (Envio de E-mails)
      - N8N_SMTP_SENDER=$email_smtp_n8n
      - N8N_SMTP_USER=$usuario_smtp_n8n
      - N8N_SMTP_PASS=$senha_smtp_n8n
      - N8N_SMTP_HOST=$host_smtp_n8n
      - N8N_SMTP_PORT=$porta_smtp_n8n
      - N8N_SMTP_SSL=$smtp_secure_smtp_n8n

      ## 🔁 Redis (Fila de Execução)
      - QUEUE_BULL_REDIS_HOST=n8n${1:+_$1}_redis
      - QUEUE_BULL_REDIS_PORT=6379
      - QUEUE_BULL_REDIS_DB=1

      ## 📊 Métricas
      - N8N_METRICS=true

      ## ⏱️ Execuções e Limpeza
      - EXECUTIONS_DATA_PRUNE=true
      - EXECUTIONS_DATA_MAX_AGE=336

      ## 🧠 Recursos de IA
      - N8N_AI_ENABLED=false
      - N8N_AI_PROVIDER=openai
      - N8N_AI_OPENAI_API_KEY=

      ## 🧰 Permissões em Funções Personalizadas
      - NODE_FUNCTION_ALLOW_BUILTIN=*
      - NODE_FUNCTION_ALLOW_EXTERNAL=moment,lodash

      ## 🕒 Fuso Horário
      - GENERIC_TIMEZONE=America/Sao_Paulo
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

  n8n${1:+_$1}_redis:
    image: redis:latest  ## Versão do Redis
    command: [
        "redis-server",
        "--appendonly",
        "yes",
        "--port",
        "6379"
      ]

    volumes:
      - n8n${1:+_$1}_redis:/data

    networks:
      - $nome_rede_interna ## Nome da rede interna

    ## Descomente as linhas abaixo para uso externo
    #ports:
    #  - 6379:6379

    deploy:
      placement:
        constraints:
          - node.role == manager
      resources:
        limits:
          cpus: "1"
          memory: 1024M

## --------------------------- ORION --------------------------- ##

volumes:
  n8n${1:+_$1}_redis:
    external: true
    name: n8n${1:+_$1}_redis

networks:
  $nome_rede_interna: ## Nome da rede interna
    external: true
    name: $nome_rede_interna ## Nome da rede interna
EOL
}
"""

with open(os.path.join(workspace, "assets", "SetupOrion.sh"), "w") as f:
    f.write(setup_script_content)

# Create the tools reference file
tools_content = """# Orion Design VPS Solutions

## Automation & AI
- **N8N**: Workflow automation tool (queue mode with editor, webhook, worker, redis services).
- **Flowise**: Low-code tool for building LLM apps.
- **Typebot**: Conversational form builder.

## Core Infrastructure
- **Traefik & Portainer**: Reverse proxy and Docker container management.
"""

with open(os.path.join(workspace, "references", "tools.md"), "w") as f:
    f.write(tools_content)

# Distractor files - realistic but irrelevant to the task
distractor_files = {
    "deployments/staging/flowise_v1.yaml": """version: "3.7"
services:
  flowise_staging:
    image: flowiseai/flowise:latest
    networks:
      - GlobeNetStaging
""",
    "deployments/staging/chatwoot_old.yaml": """version: "3.7"
# DEPRECATED - Do not use
services:
  chatwoot_app:
    image: chatwoot/chatwoot:v3.0.0
""",
    "deployments/production/traefik.yaml": """version: "3.7"
services:
  traefik:
    image: traefik:v2.10.0
    networks:
      - GlobeNet
""",
    "deployments/production/portainer.yaml": """version: "3.7"
services:
  portainer:
    image: portainer/portainer-ce:latest
""",
    "configs/traefik/traefik.toml": """[entryPoints]
  [entryPoints.web]
    address = ":80"
  [entryPoints.websecure]
    address = ":443"
""",
    "configs/nginx/nginx.conf": """server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}
""",
    "configs/databases/postgres_config.sql": """-- PostgreSQL configuration
CREATE DATABASE n8n_production;
CREATE USER n8n_user WITH PASSWORD 'PLACEHOLDER';
""",
    "scripts/maintenance/cleanup.sh": """#!/bin/bash
# Docker cleanup script
docker system prune -af
""",
    "scripts/backup/postgres_backup.sh": """#!/bin/bash
# Postgres backup
pg_dump -U postgres n8n_queue_prod > /backups/n8n_$(date +%Y%m%d).sql
""",
    "docs/architecture/overview.md": """# Infrastructure Architecture

## Services
- Traefik (reverse proxy)
- N8N (workflow automation)
- Postgres (database)
- Redis (queue)

## Network
All services are connected via the internal overlay network `GlobeNet`.
""",
    "docs/runbooks/n8n_ops.md": """# N8N Operations Runbook

## Scaling Workers
To scale workers: `docker service scale n8n_prod_worker=3`

## Checking logs
`docker service logs n8n_prod_editor`
""",
    "monitoring/grafana/dashboards/n8n_dashboard.json": """{
  "title": "N8N Metrics",
  "panels": []
}
""",
    "monitoring/prometheus/prometheus.yml": """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'n8n'
    static_configs:
      - targets: ['n8n_prod_editor:5678']
""",
    "deployments/testing/n8n_test_broken.yaml": """# BROKEN CONFIG - DO NOT USE
version: "3.7"
services:
  n8n:
    image: n8nio/n8n:latest
    environment:
      - N8N_HOST=test.example.com
      - EXECUTIONS_MODE=regular
""",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# Create the deployment parameters file that the agent needs to use
# This provides the business inputs for the stack
deployment_params = {
    "project": "GlobeShop E-Commerce",
    "environment": "production",
    "stack_suffix": "prod",
    "internal_network": "GlobeNet",
    "n8n_editor_domain": "n8n.globeshop.io",
    "n8n_webhook_domain": "webhook.globeshop.io",
    "postgres_password": "P0stgr3s_Gl0be_S3cur3",
    "smtp": {
        "email": "ops@globeshop.io",
        "user": "ops@globeshop.io",
        "password": "Smtp_G10be_2024",
        "host": "smtp.mailgun.org",
        "port": 587
    }
}

with open(os.path.join(workspace, "deployments", "production", "deployment_params.json"), "w") as f:
    json.dump(deployment_params, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")