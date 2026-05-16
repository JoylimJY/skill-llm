import json
import os
import random
from pathlib import Path

random.seed(42)

# ── Workspace root ──────────────────────────────────────────────────────────
workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Simulate the ~/.openclaw/ directory ────────────────────────────────────
openclaw_dir = workspace / ".openclaw"
openclaw_dir.mkdir(parents=True, exist_ok=True)

# ── Distractor files to simulate a realistic project environment ───────────
distractor_dirs = [
    workspace / "logs",
    workspace / "logs" / "archive",
    workspace / "configs" / "legacy",
    workspace / "configs" / "staging",
    workspace / "scripts",
    workspace / "references",
    workspace / "deployments" / "prod",
    workspace / "deployments" / "staging",
    workspace / "docs",
    workspace / "tmp",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractor_files = {
    workspace / "logs" / "gateway.log": "2024-01-10 10:00:00 INFO  dispatch complete (replies=1)\n2024-01-10 10:01:00 INFO  rejected: no bot mention\n",
    workspace / "logs" / "archive" / "gateway-2023.log": "old log data\n",
    workspace / "configs" / "legacy" / "openclaw_v1.json": json.dumps({"version": "1.0", "note": "deprecated"}),
    workspace / "configs" / "staging" / "openclaw_staging.json": json.dumps({"version": "2.0", "channels": {}}),
    workspace / "scripts" / "deploy.sh": "#!/bin/bash\necho 'deploying...'\n",
    workspace / "scripts" / "rollback.sh": "#!/bin/bash\necho 'rolling back...'\n",
    workspace / "references" / "architecture.md": "# Architecture\nSee main docs for details.\n",
    workspace / "references" / "troubleshooting.md": (
        "# Troubleshooting\n\n"
        "## Good specialist rejection on plain message:\n"
        "  `rejected: no bot mention`\n\n"
        "## Good coordinator silence when another bot is mentioned:\n"
        "  `dispatch complete (replies=0)`\n\n"
        "## Broken specialist delivery:\n"
        "  no inbound log lines for that account at all\n"
    ),
    workspace / "deployments" / "prod" / "manifest.yaml": "app: feishu-gateway\nversion: 3.2.1\n",
    workspace / "deployments" / "staging" / "manifest.yaml": "app: feishu-gateway\nversion: 3.3.0-rc1\n",
    workspace / "docs" / "onboarding.md": "# Onboarding\nWelcome to the team!\n",
    workspace / "tmp" / "scratch.txt": "temp notes\n",
}
for path, content in distractor_files.items():
    path.write_text(content)

# ── The REAL apply script the agent will invoke ─────────────────────────────
# This script patches openclaw.json for the company-group pattern
apply_script_path = workspace / "scripts" / "apply_feishu_group_company.py"
apply_script_content = r'''#!/usr/bin/env python3
"""
apply_feishu_group_company.py

Patches ~/.openclaw/openclaw.json to configure a Feishu multi-bot company group:
  - One coordinator bot handles all plain messages (requireMention: false)
  - Specialist bots only respond when @mentioned (requireMention: true)
  - Top-level group rule enforces requireMention: true
  - Coordinator receives a group-scoped systemPrompt enforcing NO_REPLY logic
  - Legacy 'group' key is removed and replaced with 'groups'

Usage:
    python scripts/apply_feishu_group_company.py \
        --config ~/.openclaw/openclaw.json \
        --chat-id <oc_xxx> \
        --coordinator <accountId> \
        --specialists <accountId1> [<accountId2> ...]
"""

import argparse
import json
import sys
from pathlib import Path


COORDINATOR_SYSTEM_PROMPT = (
    "You are the company coordinator bot. Rules:\n"
    "1. If no one is @mentioned in the message, reply normally.\n"
    "2. If another user or bot is @mentioned but NOT you, respond with exactly: NO_REPLY\n"
    "3. If you yourself are @mentioned, reply normally."
)


def load_config(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def save_config(path: Path, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[apply] Saved config to {path}")


def remove_legacy_group_key(account: dict) -> None:
    """Remove legacy singular 'group' key from a Feishu account config."""
    feishu = account.get("channels", {}).get("feishu", {})
    if "group" in feishu:
        del feishu["group"]
        print("[apply] Removed legacy 'group' key")


def patch_account(accounts: dict, account_id: str, chat_id: str, require_mention: bool, system_prompt: str = None) -> None:
    if account_id not in accounts:
        print(f"[apply] WARNING: account '{account_id}' not found in config, skipping", file=sys.stderr)
        return

    account = accounts[account_id]
    feishu = account.setdefault("channels", {}).setdefault("feishu", {})

    # Remove legacy key
    if "group" in feishu:
        del feishu["group"]
        print(f"[apply] Removed legacy 'group' key from account '{account_id}'")

    # Set per-account group override using 'groups' (plural)
    groups = feishu.setdefault("groups", {})
    group_cfg = groups.setdefault(chat_id, {})
    group_cfg["requireMention"] = require_mention

    if system_prompt is not None:
        group_cfg["systemPrompt"] = system_prompt

    print(f"[apply] Patched account '{account_id}': groups.{chat_id}.requireMention={require_mention}")


def patch_top_level_group_rule(config: dict, chat_id: str) -> None:
    """Set the top-level group rule requireMention: true for the chat."""
    rules = config.setdefault("groupRules", {})
    rules[chat_id] = rules.get(chat_id, {})
    rules[chat_id]["requireMention"] = True
    print(f"[apply] Set top-level groupRules.{chat_id}.requireMention=true")


def main():
    parser = argparse.ArgumentParser(description="Patch openclaw.json for Feishu company group")
    parser.add_argument("--config", required=True, help="Path to openclaw.json")
    parser.add_argument("--chat-id", required=True, help="Feishu group chat ID (oc_xxx)")
    parser.add_argument("--coordinator", required=True, help="Account ID of coordinator bot")
    parser.add_argument("--specialists", nargs="+", required=True, help="Account IDs of specialist bots")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    if not config_path.exists():
        print(f"[apply] ERROR: Config file not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    config = load_config(config_path)
    accounts = config.get("channels", {}).get("feishu", {}).get("accounts", {})

    if not accounts:
        print("[apply] ERROR: No feishu accounts found in config", file=sys.stderr)
        sys.exit(1)

    # 1. Set top-level group rule
    patch_top_level_group_rule(config, args.chat_id)

    # 2. Patch coordinator: requireMention=false + systemPrompt
    patch_account(accounts, args.coordinator, args.chat_id,
                  require_mention=False,
                  system_prompt=COORDINATOR_SYSTEM_PROMPT)

    # 3. Patch each specialist: requireMention=true
    for specialist in args.specialists:
        patch_account(accounts, specialist, args.chat_id, require_mention=True)

    save_config(config_path, config)
    print("[apply] Done.")


if __name__ == "__main__":
    main()
'''
apply_script_path.write_text(apply_script_content)
apply_script_path.chmod(0o755)

# ── The MESSY / BROKEN openclaw.json the agent must fix ─────────────────────
# Problems embedded:
#   1. company-ui and company-dev use legacy 'group' key (singular) instead of 'groups'
#   2. company-ceo has requireMention: true (wrong — coordinator should be false)
#   3. No top-level groupRules entry for oc_abc123
#   4. No systemPrompt on company-ceo for the group
#   5. company-dev has a stale 'bindings' reference to an old accountId

broken_config = {
    "version": "3.1.0",
    "gateway": {
        "port": 8080,
        "logLevel": "info"
    },
    "groupRules": {
        "oc_old_group_xyz": {
            "requireMention": True
        }
    },
    "channels": {
        "feishu": {
            "accounts": {
                "company-ceo": {
                    "displayName": "Company CEO Bot",
                    "appId": "cli_ceo_001",
                    "appSecret": "secret_ceo",
                    "channels": {
                        "feishu": {
                            # WRONG: using legacy 'group' singular key
                            "group": {
                                "oc_abc123": {
                                    "requireMention": True  # WRONG: coordinator should be false
                                }
                            }
                        }
                    }
                },
                "company-ui": {
                    "displayName": "UI Specialist Bot",
                    "appId": "cli_ui_002",
                    "appSecret": "secret_ui",
                    "channels": {
                        "feishu": {
                            # WRONG: using legacy 'group' singular key
                            "group": {
                                "oc_abc123": {
                                    "requireMention": False  # WRONG: specialist should require mention
                                }
                            }
                        }
                    }
                },
                "company-dev": {
                    "displayName": "Dev Specialist Bot",
                    "appId": "cli_dev_003",
                    "appSecret": "secret_dev",
                    "channels": {
                        "feishu": {
                            # WRONG: using legacy 'group' singular key, also wrong value
                            "group": {
                                "oc_abc123": {
                                    "requireMention": False
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "bindings": [
        {
            "name": "ceo-group-binding",
            "match": {
                "accountId": "company-ceo",
                "chatId": "oc_abc123"
            },
            "handler": "default"
        },
        {
            "name": "ui-group-binding",
            "match": {
                "accountId": "company-ui",
                "chatId": "oc_abc123"
            },
            "handler": "ui-specialist"
        },
        {
            "name": "dev-group-binding",
            "match": {
                "accountId": "company-dev",
                "chatId": "oc_abc123"
            },
            "handler": "dev-specialist"
        }
    ]
}

config_path = openclaw_dir / "openclaw.json"
config_path.write_text(json.dumps(broken_config, indent=2))

print("Workspace generation complete.")
print(f"  Config: {config_path}")
print(f"  Script: {apply_script_path}")