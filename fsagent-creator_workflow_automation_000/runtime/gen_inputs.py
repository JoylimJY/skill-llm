#!/usr/bin/env python3
"""
Build the initial sandbox workspace for the OpenClaw agent creator task.
Creates the mock scripts, initial config, and distractor files.
"""

import os
import json
import stat
import random

random.seed(42)

WORKSPACE = "/home/admin"
OPENCLAW_DIR = "/home/admin/.openclaw"
AGENTS_DIR = f"{OPENCLAW_DIR}/agents"
SCRIPTS_DIR = f"{WORKSPACE}/openclaw-scripts"

# ── 1. Create directory structure ────────────────────────────────────────────
for d in [
    OPENCLAW_DIR,
    AGENTS_DIR,
    SCRIPTS_DIR,
    f"{OPENCLAW_DIR}/logs",
    f"{OPENCLAW_DIR}/tmp",
    f"{WORKSPACE}/docs",
    f"{WORKSPACE}/configs",
    f"{WORKSPACE}/backup",
    f"{WORKSPACE}/deploy",
    f"{WORKSPACE}/deploy/prod",
    f"{WORKSPACE}/deploy/staging",
]:
    os.makedirs(d, exist_ok=True)

# ── 2. Initial openclaw.json  ─────────────────────────────────────────────────
# A "main" agent already exists. This is the protected one.
initial_config = {
    "version": "2.1.0",
    "gateway": {
        "port": 8080,
        "host": "0.0.0.0"
    },
    "agents": {
        "list": ["main"]
    },
    "channels": {
        "feishu": {
            "accounts": {
                "main": {
                    "appId": "cli_main000000",
                    "appSecret": "mainsecret000"
                }
            }
        }
    },
    "bindings": [
        {
            "channel": "feishu",
            "account": "main",
            "agent": "main"
        }
    ],
    "tools": {
        "agentToAgent": {
            "allow": ["main"]
        }
    }
}

with open(f"{OPENCLAW_DIR}/openclaw.json", "w") as f:
    json.dump(initial_config, f, indent=2, ensure_ascii=False)

# ── 3. Create main agent directory (already exists) ───────────────────────────
os.makedirs(f"{AGENTS_DIR}/main/agent", exist_ok=True)
os.makedirs(f"{AGENTS_DIR}/main/sessions", exist_ok=True)
with open(f"{AGENTS_DIR}/main/agent/config.json", "w") as f:
    json.dump({"id": "main", "name": "主机器人"}, f)

# workspace for main
main_ws = f"{OPENCLAW_DIR}/workspace-main"
os.makedirs(main_ws, exist_ok=True)
for fname in ["AGENTS.md", "SOUL.md", "USER.md"]:
    with open(f"{main_ws}/{fname}", "w") as f:
        f.write(f"# {fname}\nMain agent workspace file.\n")

# ── 4. models.json (to be copied by create-agent.sh) ─────────────────────────
models_config = {
    "models": [
        {"id": "glm-5", "provider": "zhipu"},
        {"id": "qwen3.5-plus", "provider": "alibaba"},
        {"id": "deepseek-v3", "provider": "deepseek"}
    ]
}
with open(f"{OPENCLAW_DIR}/models.json", "w") as f:
    json.dump(models_config, f, indent=2)

# ── 5. Mock gateway restart state file ───────────────────────────────────────
with open(f"{OPENCLAW_DIR}/.gateway_restart_count", "w") as f:
    f.write("0")

# ── 6. Distractor files (realistic noise) ────────────────────────────────────
# Old backup configs
with open(f"{WORKSPACE}/backup/openclaw.json.bak", "w") as f:
    json.dump({"version": "1.9.0", "agents": {"list": ["main", "oldbot"]}}, f)

# Deployment notes
with open(f"{WORKSPACE}/deploy/prod/deploy.log", "w") as f:
    f.write("2024-01-15 10:00 - Deployed v2.1.0\n2024-01-16 09:30 - Gateway restarted\n")

with open(f"{WORKSPACE}/deploy/staging/config.yaml", "w") as f:
    f.write("env: staging\nport: 9090\nfeishu_webhook: https://open.feishu.cn/...\n")

# Fake agent creation docs (wrong/misleading)
with open(f"{WORKSPACE}/docs/old-agent-guide.txt", "w") as f:
    f.write(
        "DEPRECATED: Old agent creation:\n"
        "  python3 create_agent.py --name <name> --id <id>\n"
        "  NOTE: This format is no longer used.\n"
    )

with open(f"{WORKSPACE}/docs/feishu-setup.md", "w") as f:
    f.write("# Feishu Integration\nRefer to Feishu open platform for app creation.\n")

# Configs directory noise
with open(f"{WORKSPACE}/configs/gateway.conf", "w") as f:
    f.write("[gateway]\nport=8080\nworkers=4\n")

with open(f"{WORKSPACE}/configs/logging.conf", "w") as f:
    f.write("[logging]\nlevel=INFO\nfile=/home/admin/.openclaw/logs/gateway.log\n")

# Scripts dir noise
with open(f"{SCRIPTS_DIR}/README.txt", "w") as f:
    f.write("OpenClaw management scripts. Use create-agent.sh, delete-agent.sh, list-agents.sh.\n")

with open(f"{SCRIPTS_DIR}/old-migrate.sh", "w") as f:
    f.write("#!/bin/bash\n# DEPRECATED migration script\necho 'Use new scripts instead'\n")

# ── 7. Write the actual mock scripts ─────────────────────────────────────────
# These simulate what the real scripts do to the filesystem

CREATE_AGENT_SCRIPT = r"""#!/bin/bash
set -e

AGENT_ID="$1"
AGENT_NAME="$2"
APP_ID="$3"
APP_SECRET="$4"
MODEL="${5:-glm-5}"
DESCRIPTION="${6:-}"

if [ -z "$AGENT_ID" ] || [ -z "$AGENT_NAME" ] || [ -z "$APP_ID" ] || [ -z "$APP_SECRET" ]; then
    echo "Usage: $0 <agent-id> <agent-name> <app-id> <app-secret> [model] [description]"
    exit 1
fi

OPENCLAW_DIR="/home/admin/.openclaw"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"

# Check if agent already exists
if python3 -c "
import json, sys
with open('$CONFIG_FILE') as f:
    c = json.load(f)
if '$AGENT_ID' in c['agents']['list']:
    sys.exit(1)
" 2>/dev/null; then
    :
else
    echo "Error: Agent '$AGENT_ID' already exists."
    exit 1
fi

# Create directory structure
mkdir -p "$OPENCLAW_DIR/agents/$AGENT_ID/agent"
mkdir -p "$OPENCLAW_DIR/agents/$AGENT_ID/sessions"

# Create workspace
WORKSPACE="$OPENCLAW_DIR/workspace-$AGENT_ID"
mkdir -p "$WORKSPACE"
touch "$WORKSPACE/AGENTS.md"
touch "$WORKSPACE/SOUL.md"
touch "$WORKSPACE/USER.md"
touch "$WORKSPACE/TOOLS.md"
touch "$WORKSPACE/CONTEXT.md"

# Copy models.json
cp "$OPENCLAW_DIR/models.json" "$OPENCLAW_DIR/agents/$AGENT_ID/models.json"

# Update openclaw.json
python3 << PYEOF
import json

config_path = "$CONFIG_FILE"
with open(config_path, 'r') as f:
    config = json.load(f)

agent_id = "$AGENT_ID"
agent_name = "$AGENT_NAME"
app_id = "$APP_ID"
app_secret = "$APP_SECRET"
model = "$MODEL"
description = "$DESCRIPTION"

# Add to agents.list
if agent_id not in config['agents']['list']:
    config['agents']['list'].append(agent_id)

# Add feishu account
config['channels']['feishu']['accounts'][agent_id] = {
    'appId': app_id,
    'appSecret': app_secret
}

# Add binding
config['bindings'].append({
    'channel': 'feishu',
    'account': agent_id,
    'agent': agent_id
})

# Add to agentToAgent.allow
if agent_id not in config['tools']['agentToAgent']['allow']:
    config['tools']['agentToAgent']['allow'].append(agent_id)

# Write agent config
import os, json as j
agent_cfg = {
    'id': agent_id,
    'name': agent_name,
    'model': model,
    'description': description
}
with open(f'/home/admin/.openclaw/agents/{agent_id}/agent/config.json', 'w') as af:
    j.dump(agent_cfg, af, indent=2, ensure_ascii=False)

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f'Agent {agent_id} ({agent_name}) created successfully.')
PYEOF

echo "Agent '$AGENT_ID' created. Remember to run: openclaw gateway restart"
"""

DELETE_AGENT_SCRIPT = r"""#!/bin/bash
set -e

AGENT_ID="$1"

if [ -z "$AGENT_ID" ]; then
    echo "Usage: $0 <agent-id>"
    exit 1
fi

if [ "$AGENT_ID" = "main" ]; then
    echo "Error: Cannot delete the main agent."
    exit 1
fi

OPENCLAW_DIR="/home/admin/.openclaw"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"

# Check agent exists
if ! python3 -c "
import json, sys
with open('$CONFIG_FILE') as f:
    c = json.load(f)
if '$AGENT_ID' not in c['agents']['list']:
    sys.exit(1)
" 2>/dev/null; then
    echo "Error: Agent '$AGENT_ID' not found."
    exit 1
fi

# Remove from config
python3 << PYEOF
import json

config_path = "$CONFIG_FILE"
with open(config_path, 'r') as f:
    config = json.load(f)

agent_id = "$AGENT_ID"

# Remove from agents.list
config['agents']['list'] = [a for a in config['agents']['list'] if a != agent_id]

# Remove feishu account
config['channels']['feishu']['accounts'].pop(agent_id, None)

# Remove bindings
config['bindings'] = [b for b in config['bindings'] if b.get('agent') != agent_id]

# Remove from agentToAgent.allow
config['tools']['agentToAgent']['allow'] = [
    a for a in config['tools']['agentToAgent']['allow'] if a != agent_id
]

with open(config_path, 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print(f'Agent {agent_id} removed from config.')
PYEOF

# Remove directories
rm -rf "$OPENCLAW_DIR/agents/$AGENT_ID"
rm -rf "$OPENCLAW_DIR/workspace-$AGENT_ID"

echo "Agent '$AGENT_ID' deleted. Remember to run: openclaw gateway restart"
"""

LIST_AGENTS_SCRIPT = r"""#!/bin/bash
OPENCLAW_DIR="/home/admin/.openclaw"
CONFIG_FILE="$OPENCLAW_DIR/openclaw.json"

python3 << PYEOF
import json
with open("$CONFIG_FILE") as f:
    config = json.load(f)

agents = config['agents']['list']
print(f"Total agents: {len(agents)}")
for agent_id in agents:
    feishu = config['channels']['feishu']['accounts'].get(agent_id, {})
    print(f"  - {agent_id} | appId: {feishu.get('appId','N/A')}")
PYEOF
"""

OPENCLAW_GATEWAY_SCRIPT = r"""#!/bin/bash
# Mock openclaw gateway command
ACTION="$1"
SUBACTION="$2"

if [ "$ACTION" = "gateway" ] && [ "$SUBACTION" = "restart" ]; then
    COUNT_FILE="/home/admin/.openclaw/.gateway_restart_count"
    CURRENT=$(cat "$COUNT_FILE" 2>/dev/null || echo "0")
    NEW_COUNT=$((CURRENT + 1))
    echo "$NEW_COUNT" > "$COUNT_FILE"
    echo "Gateway restarting... [restart #$NEW_COUNT]"
    echo "Gateway started successfully on port 8080."
else
    echo "Usage: openclaw gateway restart"
    exit 1
fi
"""

scripts = {
    f"{WORKSPACE}/create-agent.sh": CREATE_AGENT_SCRIPT,
    f"{WORKSPACE}/delete-agent.sh": DELETE_AGENT_SCRIPT,
    f"{WORKSPACE}/list-agents.sh": LIST_AGENTS_SCRIPT,
    f"{WORKSPACE}/openclaw": OPENCLAW_GATEWAY_SCRIPT,
}

for path, content in scripts.items():
    with open(path, "w") as f:
        f.write(content)
    os.chmod(path, 0o755)

# Also place in /usr/local/bin for PATH access
for name in ["openclaw"]:
    src = f"{WORKSPACE}/{name}"
    dst = f"/usr/local/bin/{name}"
    import shutil
    shutil.copy2(src, dst)
    os.chmod(dst, 0o755)

print("Workspace initialized successfully.")
print(f"Scripts in: {WORKSPACE}")
print(f"Config: {OPENCLAW_DIR}/openclaw.json")