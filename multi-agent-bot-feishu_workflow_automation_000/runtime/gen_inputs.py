import json
import os
import random

random.seed(42)

# Create the base openclaw directory structure
home = os.path.expanduser("~")
openclaw_dir = os.path.join(home, ".openclaw")
os.makedirs(openclaw_dir, exist_ok=True)

# Create existing workspace for the default sales agent
workspace_sales = os.path.join(openclaw_dir, "workspace-sales")
os.makedirs(workspace_sales, exist_ok=True)

# Create a realistic existing openclaw.json with a pre-existing agent and binding
# This is intentionally messy: the accounts key exists but has only one entry,
# bindings is a list with one entry, agents.list has one agent.
existing_config = {
    "version": "1.2.0",
    "agents": {
        "list": [
            {
                "id": "sales",
                "name": "销售助手",
                "workspace": "~/.openclaw/workspace-sales",
                "model": {
                    "primary": "ark/doubao"
                },
                "default": True
            }
        ]
    },
    "channels": {
        "feishu": {
            "accounts": {
                "sales-bot": {
                    "appId": "cli_sales123abc",
                    "appSecret": "salesSecretXYZ789",
                    "botName": "销售小助手",
                    "dmPolicy": "open",
                    "allowFrom": []
                }
            }
        }
    },
    "bindings": [
        {
            "agentId": "sales",
            "match": {
                "channel": "feishu",
                "accountId": "sales-bot"
            }
        }
    ]
}

config_path = os.path.join(openclaw_dir, "openclaw.json")
with open(config_path, "w", encoding="utf-8") as f:
    json.dump(existing_config, f, ensure_ascii=False, indent=2)

# Create distractor files to simulate a realistic workspace
distractor_files = [
    ("logs/gateway.log", "2024-01-15 10:23:11 INFO  Gateway started\n2024-01-15 10:23:12 INFO  Agent sales loaded\n2024-01-15 10:23:13 INFO  Feishu channel connected\n"),
    ("logs/error.log", "2024-01-14 09:10:05 ERROR Connection timeout\n2024-01-14 09:10:06 WARN  Retrying...\n"),
    ("references/config-template.json", json.dumps({
        "version": "x.x.x",
        "agents": {"list": []},
        "channels": {"feishu": {"accounts": {}}},
        "bindings": []
    }, indent=2)),
    ("workspace-sales/memory.db", "SQLITE_PLACEHOLDER_DATA"),
    ("workspace-sales/context.json", json.dumps({"conversations": [], "lastUpdated": "2024-01-15"})),
    ("workspace-sales/preferences.json", json.dumps({"language": "zh-CN", "timezone": "Asia/Shanghai"})),
    ("backups/openclaw.json.bak.20240114", json.dumps(existing_config, ensure_ascii=False, indent=2)),
    ("backups/openclaw.json.bak.20240101", '{"version":"1.1.0","agents":{"list":[]},"channels":{},"bindings":[]}'),
    ("scripts/restart.sh", "#!/bin/bash\necho 'Restarting OpenClaw gateway...'\nopenclaw gateway restart\n"),
    ("scripts/backup.sh", "#!/bin/bash\ncp ~/.openclaw/openclaw.json ~/.openclaw/backups/openclaw.json.bak.$(date +%Y%m%d)\n"),
    ("tmp/pending_messages.json", json.dumps([{"id": "msg001", "from": "user_abc", "content": "hello"}])),
    ("tmp/session_cache.json", json.dumps({"sessions": {}, "ttl": 3600})),
]

for rel_path, content in distractor_files:
    full_path = os.path.join(openclaw_dir, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Create a fake openclaw CLI stub so gateway restart can be "called"
bin_dir = "/usr/local/bin"
openclaw_stub = os.path.join(bin_dir, "openclaw")
with open(openclaw_stub, "w") as f:
    f.write("#!/bin/bash\necho \"openclaw: command '$@' executed\"\nexit 0\n")
os.chmod(openclaw_stub, 0o755)

print("Workspace generated successfully.")
print(f"Config path: {config_path}")
print(f"Distractor files created: {len(distractor_files)}")