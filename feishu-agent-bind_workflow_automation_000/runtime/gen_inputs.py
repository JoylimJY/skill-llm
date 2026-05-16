#!/usr/bin/env python3
import json
import os
import random

random.seed(42)

HOME = os.path.expanduser("~")
OPENCLAW_DIR = os.path.join(HOME, ".openclaw")

# --- Create main openclaw directory structure ---
os.makedirs(os.path.join(OPENCLAW_DIR, "workspace", "memory"), exist_ok=True)
os.makedirs(os.path.join(OPENCLAW_DIR, "workspace-hr", "memory"), exist_ok=True)
os.makedirs(os.path.join(OPENCLAW_DIR, "agents", "hr", "sessions"), exist_ok=True)
os.makedirs(os.path.join(OPENCLAW_DIR, "agents", "devops", "sessions"), exist_ok=True)
os.makedirs(os.path.join(OPENCLAW_DIR, "agents", "main", "sessions"), exist_ok=True)
os.makedirs(os.path.join(OPENCLAW_DIR, "logs"), exist_ok=True)
os.makedirs(os.path.join(OPENCLAW_DIR, "plugins"), exist_ok=True)

# --- Main workspace files (shared — devops currently points here) ---
with open(os.path.join(OPENCLAW_DIR, "workspace", "SOUL.md"), "w") as f:
    f.write("# Main Agent Soul\nYou are the main OpenClaw assistant.\n")

with open(os.path.join(OPENCLAW_DIR, "workspace", "AGENTS.md"), "w") as f:
    f.write("# Agents\n- main: General assistant\n")

with open(os.path.join(OPENCLAW_DIR, "workspace", "BOOTSTRAP.md"), "w") as f:
    f.write("# Bootstrap\nInitialize main agent context.\n")

# --- HR workspace files ---
with open(os.path.join(OPENCLAW_DIR, "workspace-hr", "SOUL.md"), "w") as f:
    f.write("# HR Agent Soul\nYou are the HR assistant. Help with people operations.\n")

with open(os.path.join(OPENCLAW_DIR, "workspace-hr", "AGENTS.md"), "w") as f:
    f.write("# Agents\n- hr: Human Resources assistant\n")

# --- The main openclaw.json config (messy, realistic state) ---
DEVOPS_CHAT_ID = "oc_d3f4a8b2c1e5f6a7b8c9d0e1"
HR_CHAT_ID = "oc_a1b2c3d4e5f6a7b8c9d0e1f2"

config = {
    "version": "2.1.0",
    "gateway": {
        "port": 8080,
        "host": "0.0.0.0",
        "debug": False
    },
    "agents": {
        "list": [
            {
                "id": "main",
                "name": "Main Assistant",
                "workspace": os.path.join(OPENCLAW_DIR, "workspace"),
                "model": "gpt-4o"
            },
            {
                "id": "hr",
                "name": "HR Assistant",
                "workspace": os.path.join(OPENCLAW_DIR, "workspace-hr"),
                "model": "gpt-4o-mini"
            },
            {
                "id": "devops",
                "name": "DevOps Assistant",
                # PROBLEM: devops shares the main workspace — must be fixed
                "workspace": os.path.join(OPENCLAW_DIR, "workspace"),
                "model": "gpt-4o"
            }
        ]
    },
    "channels": {
        "feishu": {
            "accountId": "main",
            "appId": "cli_a1b2c3d4e5f6g7h8",
            "appSecret": "REDACTED",
            "groups": {
                HR_CHAT_ID: {"requireMention": False}
            }
        },
        "slack": {
            "enabled": False
        }
    },
    "bindings": [
        {
            "agentId": "hr",
            "match": {
                "channel": "feishu",
                "peer": {"kind": "group", "id": HR_CHAT_ID},
                "accountId": "main"
            }
        }
        # NOTE: devops binding intentionally missing — agent must add it
    ],
    "sessions": {
        "ttl": 3600,
        "maxPerAgent": 100
    },
    "memory": {
        "backend": "local",
        "path": os.path.join(OPENCLAW_DIR, "workspace", "memory")
    }
}

with open(os.path.join(OPENCLAW_DIR, "openclaw.json"), "w") as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

# --- HR agent sessions: contains a stale session for the DevOps chat group ---
hr_sessions = {
    f"feishu:group:{HR_CHAT_ID}:session_001": {
        "agentId": "hr",
        "createdAt": "2024-01-10T09:00:00Z",
        "messages": [{"role": "user", "content": "Leave request"}]
    },
    f"feishu:group:{DEVOPS_CHAT_ID}:session_stale": {
        "agentId": "hr",
        "createdAt": "2024-01-09T14:22:00Z",
        "messages": [{"role": "user", "content": "kubectl get pods"}]
    },
    f"feishu:group:{DEVOPS_CHAT_ID}:session_old2": {
        "agentId": "hr",
        "createdAt": "2024-01-08T11:05:00Z",
        "messages": [{"role": "user", "content": "deploy to prod?"}]
    }
}

with open(os.path.join(OPENCLAW_DIR, "agents", "hr", "sessions", "sessions.json"), "w") as f:
    json.dump(hr_sessions, f, indent=2)

# --- Main agent sessions: no stale entries for devops chat ---
main_sessions = {
    "feishu:group:oc_main_group_001:session_001": {
        "agentId": "main",
        "createdAt": "2024-01-10T10:00:00Z",
        "messages": []
    }
}

with open(os.path.join(OPENCLAW_DIR, "agents", "main", "sessions", "sessions.json"), "w") as f:
    json.dump(main_sessions, f, indent=2)

# --- DevOps agent sessions: empty initially ---
with open(os.path.join(OPENCLAW_DIR, "agents", "devops", "sessions", "sessions.json"), "w") as f:
    json.dump({}, f, indent=2)

# --- Distractor files to simulate realistic environment ---
with open(os.path.join(OPENCLAW_DIR, "logs", "gateway-2024-01-10.log"), "w") as f:
    f.write("[INFO] Gateway started on port 8080\n[INFO] Feishu plugin loaded: account=main\n[WARN] Session cache miss for group oc_d3f4a8b2c1e5f6a7b8c9d0e1\n")

with open(os.path.join(OPENCLAW_DIR, "logs", "gateway-2024-01-09.log"), "w") as f:
    f.write("[INFO] Binding matched: hr -> feishu:group:oc_a1b2c3d4e5f6a7b8c9d0e1f2\n[WARN] No binding for feishu:group:oc_d3f4a8b2c1e5f6a7b8c9d0e1, falling back to main\n")

with open(os.path.join(OPENCLAW_DIR, "plugins", "feishu.json"), "w") as f:
    json.dump({"name": "feishu", "version": "1.4.2", "accountId": "main"}, f, indent=2)

os.makedirs(os.path.join(OPENCLAW_DIR, "plugins", "slack"), exist_ok=True)
with open(os.path.join(OPENCLAW_DIR, "plugins", "slack", "config.json"), "w") as f:
    json.dump({"enabled": False}, f)

with open(os.path.join(OPENCLAW_DIR, "workspace", "memory", "context.json"), "w") as f:
    json.dump({"history": [], "lastUpdated": "2024-01-10T08:00:00Z"}, f)

with open(os.path.join(OPENCLAW_DIR, "workspace-hr", "memory", "context.json"), "w") as f:
    json.dump({"history": [], "lastUpdated": "2024-01-10T09:30:00Z"}, f)

# --- Workspace: a fake migration notes file (distractor) ---
with open(os.path.join(OPENCLAW_DIR, "workspace", "MIGRATION_NOTES.txt"), "w") as f:
    f.write("Migrated from v1.x to v2.x on 2024-01-01.\nOld bindings format used 'target' instead of 'agentId'.\n")

# --- Print summary ---
print("=== Sandbox Setup Complete ===")
print(f"DevOps Chat ID (to be routed): {DEVOPS_CHAT_ID}")
print(f"HR Chat ID (existing binding): {HR_CHAT_ID}")
print(f"Config: {os.path.join(OPENCLAW_DIR, 'openclaw.json')}")
print(f"Stale sessions in HR agent: feishu:group:{DEVOPS_CHAT_ID}:* (2 entries)")
print("Problem state:")
print("  - devops agent workspace = shared main workspace (must be isolated)")
print("  - no binding for devops -> devops chat group")
print("  - stale sessions for devops chat group under HR agent")