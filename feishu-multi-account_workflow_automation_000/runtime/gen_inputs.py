import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Distractor directory structure ---
distractor_dirs = [
    "logs/gateway",
    "logs/agents",
    "agents/primary/workspace",
    "agents/escalation/workspace",
    "channels/feishu/webhooks",
    "channels/slack/webhooks",
    "backup/configs",
    "scripts/deploy",
    "docs/architecture",
    "tmp/sessions",
]
for d in distractor_dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "logs/gateway/gateway-2024-01-15.log": "INFO: gateway started\nINFO: feishu channel initialized\nWARN: no bindings found for account sub1\n",
    "logs/gateway/gateway-2024-01-16.log": "INFO: dispatching to agent (session=agent:main:main)\nWARN: routing mismatch detected\n",
    "logs/agents/agent-main.log": "Agent A initialized\nListening on feishu channel\n",
    "logs/agents/agent-sub1.log": "Agent B initialized\nWaiting for bindings...\n",
    "agents/primary/workspace/context.txt": "Primary support agent context\nHandles tier-1 customer queries\n",
    "agents/escalation/workspace/context.txt": "Escalation specialist context\nHandles tier-2 and VIP complaints\n",
    "channels/feishu/webhooks/hooks.txt": "webhook endpoint: /feishu/event\nverification: sha256\n",
    "channels/slack/webhooks/hooks.txt": "webhook endpoint: /slack/event\n",
    "backup/configs/openclaw.json.bak": json.dumps({
        "routing": [
            {"agentId": "main", "match": {"channel": "feishu", "account": "main"}},
        ],
        "agents": {"list": [{"id": "main", "name": "Agent A"}]},
        "channels": {"feishu": {"enabled": True}}
    }, indent=2),
    "scripts/deploy/restart.sh": "#!/bin/bash\nopenclaw gateway restart\n",
    "docs/architecture/overview.md": "# Architecture\nTwo Feishu bots, two agents, message routing via bindings.\n",
    "tmp/sessions/session_cache.json": json.dumps({"sessions": [], "ttl": 3600}),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE BROKEN CONFIG: openclaw.json ---
# Intentional errors:
# 1. 'bindings' is MISSING from top-level (completely absent)
# 2. There is a 'routing' key (wrong name) placed INSIDE 'channels' (wrong location)
# 3. The routing inside channels only covers 'sub1', not 'main' (missing main binding)
# 4. 'agents.list' is missing the 'default: true' field for main agent
# 5. 'agents.list' sub1 entry is missing 'workspace' field
# 6. channels.feishu.accounts is missing the 'default' policy sub-key entirely
# 7. accountId in the wrong routing uses 'account' instead of 'accountId'

broken_config = {
    "agents": {
        "list": [
            {
                "id": "main",
                "name": "Agent A"
                # missing "default": true
            },
            {
                "id": "sub1",
                "name": "Agent B"
                # missing "workspace": "/path/to/workspace-sub1"
            }
        ]
    },
    "channels": {
        "feishu": {
            "enabled": True,
            "domain": "feishu",
            "accounts": {
                "main": {
                    "appId": "cli_aAbBcCdD1234",
                    "appSecret": "secret_main_XYZ789"
                },
                "sub1": {
                    "appId": "cli_eEfFgGhH5678",
                    "appSecret": "secret_sub1_ABC123",
                    "botname": "Escalation Bot"
                }
                # missing "default": { "groupPolicy": "allowlist", ... }
            },
            # Wrong: 'routing' inside channels, wrong key name, missing main, wrong field 'account' vs 'accountId'
            "routing": [
                {
                    "agentId": "sub1",
                    "match": {
                        "channel": "feishu",
                        "account": "sub1"
                    }
                }
            ]
        },
        "slack": {
            "enabled": False
        }
    },
    "server": {
        "port": 8080,
        "host": "0.0.0.0"
    },
    "logging": {
        "level": "info",
        "path": "/tmp/openclaw"
    }
}

config_path = os.path.join(workspace, "openclaw.json")
with open(config_path, "w") as f:
    json.dump(broken_config, f, indent=2)

print(f"Workspace created at: {workspace}")
print(f"Broken config written to: {config_path}")
print("Distractor files created:")
for p in distractor_files:
    print(f"  {p}")