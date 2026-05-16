#!/usr/bin/env python3
"""
Generate sandbox workspace with:
- A realistic, deeply nested project structure (distractor files)
- An existing openclaw.json with a pre-existing agent, account, binding
- The upsert_openclaw_agent.py script in skills/openclaw-create-agent/scripts/
"""

import json
import os
import random
import shutil
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ------------------------------------------------------------------
# 1. Create deeply nested project structure (distractors)
# ------------------------------------------------------------------
distractor_dirs = [
    "src/logistics/routing",
    "src/logistics/dispatch",
    "src/api/feishu",
    "src/api/internal",
    "infra/docker",
    "infra/k8s/manifests",
    "infra/monitoring",
    "docs/runbooks",
    "docs/architecture",
    "tests/unit",
    "tests/integration",
    "config/envs/prod",
    "config/envs/staging",
    "scripts/migration",
]

for d in distractor_dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

distractor_files = {
    "src/logistics/routing/optimizer.py": '# Route optimization logic\nclass RouteOptimizer:\n    pass\n',
    "src/logistics/dispatch/scheduler.py": '# Dispatch scheduler\nimport datetime\n',
    "src/api/feishu/webhook.py": '# Feishu webhook handler\nfrom flask import Flask\napp = Flask(__name__)\n',
    "src/api/internal/health.py": '# Health check endpoint\ndef check(): return "ok"\n',
    "infra/docker/Dockerfile.api": 'FROM python:3.11\nCOPY . /app\n',
    "infra/k8s/manifests/deployment.yaml": 'apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: logistics-api\n',
    "infra/monitoring/alerts.yaml": 'groups:\n  - name: api\n    rules: []\n',
    "docs/runbooks/incident_response.md": '# Incident Response\n\n## P1 Response\n...\n',
    "docs/architecture/system_overview.md": '# System Overview\n\nThe logistics platform uses Feishu for team comm.\n',
    "tests/unit/test_optimizer.py": 'import pytest\n\ndef test_placeholder():\n    assert True\n',
    "tests/integration/test_dispatch.py": 'import pytest\n\ndef test_integration_placeholder():\n    assert True\n',
    "config/envs/prod/settings.yaml": 'debug: false\nlog_level: info\nfeishu_webhook_url: https://open.feishu.cn/...\n',
    "config/envs/staging/settings.yaml": 'debug: true\nlog_level: debug\n',
    "scripts/migration/migrate_v1_to_v2.py": '# Migration script\nprint("migrating...")\n',
    "infra/k8s/manifests/service.yaml": 'apiVersion: v1\nkind: Service\nmetadata:\n  name: logistics-svc\n',
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ------------------------------------------------------------------
# 2. Create the skill directory structure with scripts
# ------------------------------------------------------------------
skill_dir = WORKSPACE / "skills" / "openclaw-create-agent"
scripts_dir = skill_dir / "scripts"
refs_dir = skill_dir / "references"
scripts_dir.mkdir(parents=True, exist_ok=True)
refs_dir.mkdir(parents=True, exist_ok=True)

# Write the upsert script (proprietary, bundled)
upsert_script = r'''#!/usr/bin/env python3
"""
upsert_openclaw_agent.py

Upsert OpenClaw agent configuration in openclaw.json.
Handles channel account creation, binding creation, and dmScope enforcement.
"""

import argparse
import json
import sys
from pathlib import Path


def load_config(path):
    with open(path) as f:
        return json.load(f)


def save_config(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Config saved to {path}")


def upsert_account(config, account_id, app_id=None, app_secret=None, bot_name=None):
    channel = "feishu"
    config.setdefault("channels", {}).setdefault(channel, {}).setdefault("accounts", {})
    accounts = config["channels"][channel]["accounts"]
    existing = accounts.get(account_id, {})
    if app_id is not None:
        existing["app_id"] = app_id
    if app_secret is not None:
        existing["app_secret"] = app_secret
    if bot_name is not None:
        existing["bot_name"] = bot_name
    accounts[account_id] = existing
    return f"Account '{account_id}' upserted in channels.feishu.accounts"


def upsert_binding_account(config, agent_id, account_id):
    channel = "feishu"
    bindings = config.setdefault("bindings", [])
    # Check for route conflict
    for b in bindings:
        if b.get("channel") == channel and b.get("account_id") == account_id and b.get("routing_mode") == "account":
            if b.get("agent_id") != agent_id:
                print(f"ERROR: Route conflict - account '{account_id}' already bound to agent '{b['agent_id']}'", file=sys.stderr)
                sys.exit(3)
    # Remove existing binding for this agent (same channel + account mode)
    config["bindings"] = [
        b for b in bindings
        if not (b.get("agent_id") == agent_id and b.get("channel") == channel and b.get("routing_mode") == "account")
    ]
    config["bindings"].append({
        "agent_id": agent_id,
        "channel": channel,
        "routing_mode": "account",
        "account_id": account_id,
    })
    return f"Binding added: agent='{agent_id}' channel='feishu' routing_mode='account' account_id='{account_id}'"


def upsert_binding_peer(config, agent_id, peer_kind, peer_id, account_id=None):
    channel = "feishu"
    bindings = config.setdefault("bindings", [])
    # Check for route conflict
    for b in bindings:
        if b.get("channel") == channel and b.get("peer_id") == peer_id and b.get("routing_mode") == "peer":
            if b.get("agent_id") != agent_id:
                print(f"ERROR: Route conflict - peer '{peer_id}' already bound to agent '{b['agent_id']}'", file=sys.stderr)
                sys.exit(3)
    # Remove existing binding for this agent+peer
    config["bindings"] = [
        b for b in bindings
        if not (b.get("agent_id") == agent_id and b.get("channel") == channel
                and b.get("routing_mode") == "peer" and b.get("peer_id") == peer_id)
    ]
    entry = {
        "agent_id": agent_id,
        "channel": channel,
        "routing_mode": "peer",
        "peer_kind": peer_kind,
        "peer_id": peer_id,
    }
    if account_id:
        entry["account_id"] = account_id
    config["bindings"].append(entry)
    return f"Binding added: agent='{agent_id}' channel='feishu' routing_mode='peer' peer_kind='{peer_kind}' peer_id='{peer_id}'"


def enforce_dm_scope(config):
    config.setdefault("session", {})
    old = config["session"].get("dmScope")
    config["session"]["dmScope"] = "per-account-channel-peer"
    if old != "per-account-channel-peer":
        return f"dmScope changed from '{old}' to 'per-account-channel-peer'"
    return "dmScope already set correctly"


def main():
    parser = argparse.ArgumentParser(description="Upsert OpenClaw agent config")
    parser.add_argument("--config", required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--routing-mode", required=True, choices=["account", "peer"])
    parser.add_argument("--account-id")
    parser.add_argument("--app-id")
    parser.add_argument("--app-secret")
    parser.add_argument("--bot-name")
    parser.add_argument("--peer-kind", choices=["group", "direct"])
    parser.add_argument("--peer-id")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"ERROR: Config not found at {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    results = []

    if args.routing_mode == "account":
        if not args.account_id:
            print("ERROR: --account-id is required for account routing mode", file=sys.stderr)
            sys.exit(1)
        msg = upsert_account(config, args.account_id, args.app_id, args.app_secret, args.bot_name)
        results.append(msg)
        msg = upsert_binding_account(config, args.agent_id, args.account_id)
        results.append(msg)
    elif args.routing_mode == "peer":
        if not args.peer_kind:
            print("ERROR: --peer-kind is required for peer routing mode", file=sys.stderr)
            sys.exit(1)
        if not args.peer_id:
            print("ERROR: --peer-id is required for peer routing mode", file=sys.stderr)
            sys.exit(1)
        msg = upsert_binding_peer(config, args.agent_id, args.peer_kind, args.peer_id, args.account_id)
        results.append(msg)

    # Always enforce dmScope
    msg = enforce_dm_scope(config)
    results.append(msg)

    save_config(config_path, config)
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
'''

(scripts_dir / "upsert_openclaw_agent.py").write_text(upsert_script)

# Write routing-modes reference
routing_modes_ref = """# Routing Modes

## account
One Feishu bot app per agent. All DMs to that bot go to one agent.
Use when each agent needs its own dedicated Feishu app credentials.

## peer
One Feishu bot, multiple groups or direct peers mapped to different agents.
Use when a single bot serves many groups, routing by group/peer id.
Requires: peer_kind (group|direct), peer_id (oc_xxxxx format).
Always requires dmScope=per-account-channel-peer.
"""
(refs_dir / "routing-modes.md").write_text(routing_modes_ref)

# ------------------------------------------------------------------
# 3. Create ~/.openclaw/openclaw.json with a pre-existing agent
# ------------------------------------------------------------------
openclaw_dir = Path("/root/.openclaw")
openclaw_dir.mkdir(parents=True, exist_ok=True)

existing_config = {
    "version": "2",
    "channels": {
        "feishu": {
            "accounts": {
                "acct-ops-001": {
                    "app_id": "cli_ops_existing_app",
                    "app_secret": "s3cr3t_existing",
                    "bot_name": "OpsBot"
                }
            }
        }
    },
    "bindings": [
        {
            "agent_id": "ops-assistant",
            "channel": "feishu",
            "routing_mode": "account",
            "account_id": "acct-ops-001"
        }
    ],
    "session": {
        "dmScope": "global",
        "timeout": 3600
    },
    "agents": {
        "ops-assistant": {
            "workspace": "/workspace/agents/ops-assistant",
            "model": "gpt-4o"
        }
    }
}

(openclaw_dir / "openclaw.json").write_text(json.dumps(existing_config, indent=2))

# Create workspace for the existing agent (distractor)
ops_workspace = WORKSPACE / "agents" / "ops-assistant"
ops_workspace.mkdir(parents=True, exist_ok=True)
(ops_workspace / "config.yaml").write_text("agent: ops-assistant\nprompt: You are an ops assistant.\n")

# Create target workspace for the new agent (empty, just the dir)
new_agent_workspace = WORKSPACE / "agents" / "logistics-group-bot"
new_agent_workspace.mkdir(parents=True, exist_ok=True)
(new_agent_workspace / ".gitkeep").write_text("")

print("Workspace generation complete.")
print(f"Skill dir: {skill_dir}")
print(f"OpenClaw config: {openclaw_dir / 'openclaw.json'}")