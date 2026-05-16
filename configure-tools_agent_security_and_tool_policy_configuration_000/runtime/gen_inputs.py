import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Create deep distractor directory structure ---
dirs = [
    ".openclaw",
    ".openclaw/logs",
    ".openclaw/cache",
    ".openclaw/plugins",
    ".openclaw/plugins/lobster",
    ".openclaw/plugins/llm-task",
    "conventions",
    "agents",
    "agents/orchestrator",
    "agents/summarizer",
    "agents/notifier",
    "deployments",
    "deployments/prod",
    "deployments/staging",
    "scripts",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractor_files = {
    ".openclaw/logs/gateway.log": (
        "[2026-03-15 10:23:11] INFO gateway started\n"
        "[2026-03-15 10:23:12] INFO agent orchestrator-001 connected\n"
        "[2026-03-15 10:23:15] WARN tool exec blocked: missing allowlist entry\n"
        "[2026-03-15 10:24:00] INFO agent summarizer-002 connected\n"
    ),
    ".openclaw/cache/tool_index.json": json.dumps({
        "tools": ["read", "write", "exec", "web_search", "memory_search",
                  "session_status", "lobster", "llm-task", "notify", "ui_render"],
        "groups": {
            "runtime": ["exec", "bash", "python3", "node"],
            "web": ["web_search", "web_fetch"],
            "ui": ["ui_render", "ui_notify"],
            "messaging": ["notify", "slack_post"],
            "coding": ["read", "write", "exec", "memory_search"]
        },
        "version": "2026.3.2"
    }, indent=2),
    ".openclaw/plugins/lobster/manifest.json": json.dumps({
        "name": "lobster",
        "version": "1.2.0",
        "description": "Distributed task lobster plugin",
        "requires_opt_in": True
    }, indent=2),
    ".openclaw/plugins/llm-task/manifest.json": json.dumps({
        "name": "llm-task",
        "version": "0.8.3",
        "description": "Nested LLM task delegation plugin",
        "requires_opt_in": True
    }, indent=2),
    "conventions/tools.md": (
        "# Tools Convention\n\n"
        "## Profiles\n"
        "- `full`: all tools\n"
        "- `coding`: read, write, exec, memory_search, session_status\n"
        "- `messaging`: notify, slack_post, session_status, read\n"
        "- `minimal`: session_status, read\n\n"
        "## Groups\n"
        "- `group:runtime` — exec and interpreter binaries\n"
        "- `group:web` — web_search, web_fetch\n"
        "- `group:ui` — ui_render, ui_notify\n"
        "- `group:messaging` — notify, slack_post\n"
        "- `group:coding` — read, write, exec, memory_search\n\n"
        "## Exec Security Options\n"
        "- host: `sandbox` | `gateway`\n"
        "- security: `deny` | `allowlist` | `full`\n"
        "- ask: `on-miss` | `off`\n\n"
        "## Policy Layering\n"
        "- deny ALWAYS wins over allow\n"
        "- alsoAllow is additive (safe for plugins)\n"
        "- byProvider overrides global for that provider/model\n"
    ),
    "agents/orchestrator/agent.json": json.dumps({
        "id": "orchestrator-001",
        "name": "Main Orchestrator",
        "model": "anthropic/claude-3-5-sonnet",
        "role": "orchestrator",
        "description": "Primary workflow coordination agent"
    }, indent=2),
    "agents/summarizer/agent.json": json.dumps({
        "id": "summarizer-002",
        "name": "Document Summarizer",
        "model": "google/gemini-2.5-flash",
        "role": "worker",
        "description": "Summarizes financial documents using Gemini"
    }, indent=2),
    "agents/notifier/agent.json": json.dumps({
        "id": "notifier-003",
        "name": "Compliance Notifier",
        "model": "anthropic/claude-3-haiku",
        "role": "worker",
        "description": "Sends compliance alerts via messaging channels"
    }, indent=2),
    "deployments/prod/deployment.json": json.dumps({
        "environment": "production",
        "region": "us-east-1",
        "agents": ["orchestrator-001", "summarizer-002", "notifier-003"],
        "gateway_url": "https://gw.internal.fintech.corp:8443"
    }, indent=2),
    "deployments/staging/deployment.json": json.dumps({
        "environment": "staging",
        "region": "us-east-1",
        "agents": ["orchestrator-001"],
        "gateway_url": "https://gw-staging.internal.fintech.corp:8443"
    }, indent=2),
    "scripts/restart_gateway.sh": (
        "#!/bin/bash\n"
        "# Restart the OpenClaw gateway after config changes\n"
        "systemctl restart openclaw-gateway\n"
        "echo 'Gateway restarted'\n"
    ),
    "scripts/verify_tools.sh": (
        "#!/bin/bash\n"
        "# Verify tool access for a given agent\n"
        "# Usage: ./verify_tools.sh <agent-id>\n"
        "AGENT_ID=$1\n"
        "curl -s http://localhost:8080/api/agent/$AGENT_ID/tools\n"
    ),
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content)

# --- THE PROBLEM: A stale, badly misconfigured openclaw.json ---
# This is what the agent must FIX/REPLACE. It has wrong exec config,
# missing per-agent configs, no byProvider, no plugin alsoAllow.
bad_config = {
    "version": "2026.3.2",
    "gateway": {
        "host": "localhost",
        "port": 8080
    },
    "tools": {
        "profile": "full",
        # Missing: alsoAllow for plugins
        # Missing: byProvider for gemini
        "exec": {
            "host": "gateway",
            # Wrong security for prod orchestrator context
            "security": "full",
            "ask": "off"
        }
    },
    "agents": {
        "list": [
            {
                "id": "orchestrator-001",
                # No per-agent tool config at all
                "name": "Main Orchestrator"
            },
            {
                "id": "summarizer-002",
                "name": "Document Summarizer"
                # No tool restrictions despite being a low-trust worker
            },
            {
                "id": "notifier-003",
                "name": "Compliance Notifier"
                # No tool restrictions despite only needing messaging
            }
        ]
    }
}

config_path = os.path.join(workspace, ".openclaw", "openclaw.json")
with open(config_path, "w") as f:
    json.dump(bad_config, f, indent=2)

print("Workspace generated successfully.")
print(f"Config written to: {config_path}")