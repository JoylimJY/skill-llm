import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "logs",
    "agents/orchestrator/workspace",
    "agents/contract-reviewer/workspace",
    "agents/legal-researcher/workspace",
    "agents/case-manager/workspace",
    "configs/backups",
    "configs/drafts",
    "docs/onboarding",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────
distractors = {
    "logs/gateway.log": (
        "[2026-04-01 09:00:01] Gateway started\n"
        "[2026-04-01 09:00:02] Loading agents...\n"
        "[2026-04-01 09:00:03] ERROR: binding type 'delivery' not recognized\n"
        "[2026-04-01 09:00:04] Gateway failed to start\n"
    ),
    "configs/backups/openclaw.json.bak": json.dumps({
        "channels": {"feishu": {"accounts": {}}},
        "bindings": [],
        "agents": {"list": []}
    }, indent=2),
    "configs/drafts/partial_config.json": json.dumps({
        "channels": {
            "feishu": {
                "accounts": {
                    "orchestrator-bot": {
                        "appId": "cli_OLD111",
                        "appSecret": "oldsecret1",
                        "agent": "orchestrator-WRONG"
                    }
                }
            }
        }
    }, indent=2),
    "docs/onboarding/feishu-setup.md": (
        "# Feishu Setup Notes\n\n"
        "## Old approach (DEPRECATED)\n"
        "We used to use `type: delivery` in bindings. This no longer works.\n"
        "## New approach\n"
        "Ask the platform team for the correct binding type.\n"
    ),
    "references/architecture.md": (
        "# Architecture Overview\n\n"
        "## Three-Block Configuration Model\n\n"
        "OpenClaw uses three synchronized blocks in `openclaw.json`:\n\n"
        "### Block 1: `channels.feishu.accounts`\n"
        "Each entry maps an **accountId** (your chosen key) to Feishu credentials:\n"
        "```json\n"
        '"channels": {\n'
        '  "feishu": {\n'
        '    "accounts": {\n'
        '      "<accountId>": {\n'
        '        "appId": "cli_xxx",\n'
        '        "appSecret": "secret",\n'
        '        "agent": "<agentId>"\n'
        '      }\n'
        '    }\n'
        '  }\n'
        '}\n'
        "```\n\n"
        "### Block 2: `bindings`\n"
        "Routes messages from a Feishu account to an agent:\n"
        "```json\n"
        '"bindings": [\n'
        '  {\n'
        '    "type": "route",\n'
        '    "match": { "accountId": "<accountId>" },\n'
        '    "agent": "<agentId>"\n'
        '  }\n'
        ']\n'
        "```\n"
        "**Critical**: `type` MUST be `\"route\"`. Any other value causes gateway startup failure.\n\n"
        "### Block 3: `agents.list`\n"
        "```json\n"
        '"agents": {\n'
        '  "list": [\n'
        '    {\n'
        '      "id": "<agentId>",\n'
        '      "workspace": "agents/<agentId>/workspace",\n'
        '      "model": "gpt-4o",\n'
        '      "allowAgents": ["<other-agent-id>", ...]\n'
        '    }\n'
        '  ]\n'
        '}\n'
        "```\n\n"
        "## The accountId Consistency Rule\n\n"
        "The `accountId` string must be **identical** in:\n"
        "1. The key under `channels.feishu.accounts`\n"
        "2. The `match.accountId` field in `bindings`\n"
        "3. (Implicitly) the `agent` field must match the `id` in `agents.list`\n\n"
        "One mismatch = silent routing failure. The gateway starts but messages go nowhere.\n\n"
        "## Channel Layer Design\n\n"
        "The Gateway receives all inbound Feishu webhooks, extracts the `appId` from the "
        "payload, looks up the matching account entry, resolves the `accountId`, finds the "
        "binding, and dispatches to the correct agent. This is why all three blocks must align.\n"
    ),
    "references/build-guide.md": (
        "# Build Guide: From Zero to Multi-Bot\n\n"
        "## Step 1: Feishu Developer Console\n"
        "Create one Enterprise App per agent at open.feishu.cn. Enable Bot capability.\n\n"
        "## Step 2: Collect Credentials\n"
        "For each app: AppID (format: `cli_xxx`) and AppSecret.\n\n"
        "## Step 3: Use the Setup Helper\n"
        "```bash\n"
        "scripts/setup-feishu-bots.sh orchestrator:cli_xxx:secret1 writer:cli_yyy:secret2\n"
        "```\n"
        "This generates the three JSON blocks. Review and paste into openclaw.json.\n\n"
        "## Step 4: Configure openclaw.json\n"
        "The file must have all three blocks: channels, bindings, agents.list.\n\n"
        "## Step 5: Validate and Restart\n"
        "```bash\n"
        "openclaw doctor && openclaw gateway restart\n"
        "```\n\n"
        "## Step 6: Publish Feishu Apps\n"
        "Draft-state apps cannot receive messages. Publish each app in the developer console.\n"
    ),
    "references/routing-deep-dive.md": (
        "# Routing Deep Dive\n\n"
        "## accountId Consistency Checks\n\n"
        "Run this to verify:\n"
        "```bash\n"
        "# Check all three locations align\n"
        "jq '.channels.feishu.accounts | keys' openclaw.json\n"
        "jq '[.bindings[].match.accountId]' openclaw.json\n"
        "jq '[.agents.list[].id]' openclaw.json\n"
        "```\n"
        "All accountIds in bindings must appear as keys in accounts. "
        "All agent IDs in bindings must appear in agents.list.\n\n"
        "## Binding Rules\n\n"
        "Each binding: `{type, match, agent}`.\n"
        "- `type`: must be `\"route\"` (not `\"delivery\"`, not `\"forward\"`, not `\"pass\"`)\n"
        "- `match.accountId`: must equal the account key in channels\n"
        "- `agent`: must equal an id in agents.list\n\n"
        "## Group-Based Isolation\n\n"
        "Add `match.groupId` to restrict a binding to a specific Feishu group:\n"
        "```json\n"
        '{"type": "route", "match": {"accountId": "bot1", "groupId": "oc_abc"}, "agent": "writer"}\n'
        "```\n"
    ),
    "references/troubleshooting.md": (
        "# Troubleshooting\n\n"
        "## Gateway Won't Start\n"
        "- Check binding `type` — must be `\"route\"`, not `\"delivery\"`\n"
        "- Check for JSON syntax errors\n\n"
        "## Bot Not Responding\n"
        "- Is the Feishu App published (not draft)?\n"
        "- Does accountId match in all three blocks?\n\n"
        "## Wrong Agent Responding\n"
        "- Verify `match.accountId` in bindings matches the correct account key\n\n"
        "## Spawn Permission Error\n"
        "- Agent not in `allowAgents` of its parent orchestrator\n"
        "- Add all spawnable agents to orchestrator's `allowAgents` list\n\n"
        "## Sub-Agent Spawning Broken\n"
        "- Check `agentToAgent.enabled` — known bug #5813:\n"
        "  `agentToAgent.enabled: true` breaks all sub-agent spawning\n"
        "- Keep it `false`\n\n"
        "## Diagnostic Flowchart\n"
        "1. Gateway starts? → No: check binding type\n"
        "2. Bot receives message? → No: check app published + accountId\n"
        "3. Correct agent responds? → No: check binding match.accountId\n"
        "4. Orchestrator can spawn? → No: check allowAgents + agentToAgent.enabled\n"
    ),
    "agents/orchestrator/workspace/.gitkeep": "",
    "agents/contract-reviewer/workspace/.gitkeep": "",
    "agents/legal-researcher/workspace/.gitkeep": "",
    "agents/case-manager/workspace/.gitkeep": "",
}

for path, content in distractors.items():
    full = os.path.join(WORKSPACE, path)
    with open(full, "w") as f:
        f.write(content)

# ── the setup helper script (referenced in SKILL.md as already existing) ────
setup_script = r"""#!/usr/bin/env bash
# scripts/setup-feishu-bots.sh
# Usage: ./setup-feishu-bots.sh <agentId:appId:appSecret> ...
# Outputs three JSON blocks to stdout

ACCOUNTS="{}"
BINDINGS="["
AGENTS_LIST="["
FIRST=1

for arg in "$@"; do
  IFS=':' read -r AGENT_ID APP_ID APP_SECRET <<< "$arg"
  ACCOUNT_ID="${AGENT_ID}-bot"

  # Build accounts block
  ACCOUNTS=$(echo "$ACCOUNTS" | jq \
    --arg aid "$ACCOUNT_ID" \
    --arg appid "$APP_ID" \
    --arg secret "$APP_SECRET" \
    --arg agent "$AGENT_ID" \
    '.[$aid] = {"appId": $appid, "appSecret": $secret, "agent": $agent}')

  # Build binding
  BINDING=$(jq -n \
    --arg aid "$ACCOUNT_ID" \
    --arg agent "$AGENT_ID" \
    '{"type": "route", "match": {"accountId": $aid}, "agent": $agent}')

  if [ "$FIRST" -eq 1 ]; then
    BINDINGS="[$BINDING"
    FIRST=0
  else
    BINDINGS="$BINDINGS,$BINDING"
  fi

  # Build agent entry
  AGENT_ENTRY=$(jq -n \
    --arg id "$AGENT_ID" \
    --arg ws "agents/$AGENT_ID/workspace" \
    '{"id": $id, "workspace": $ws, "model": "gpt-4o", "allowAgents": []}')
  if [ "$FIRST" -le 1 ] && [ ${#AGENTS_LIST} -gt 1 ]; then
    AGENTS_LIST="$AGENTS_LIST,$AGENT_ENTRY"
  else
    AGENTS_LIST="[$AGENT_ENTRY"
  fi
done

BINDINGS="$BINDINGS]"
AGENTS_LIST="$AGENTS_LIST]"

echo "=== channels.feishu.accounts ==="
echo "$ACCOUNTS" | jq .
echo ""
echo "=== bindings ==="
echo "$BINDINGS" | jq .
echo ""
echo "=== agents.list ==="
echo "$AGENTS_LIST" | jq .
"""

with open(os.path.join(WORKSPACE, "scripts/setup-feishu-bots.sh"), "w") as f:
    f.write(setup_script)

# ── messy/broken existing openclaw.json ──────────────────────────────────────
# This is intentionally broken: wrong binding type, mismatched accountIds,
# missing agents, agentToAgent enabled, incomplete allowAgents
broken_config = {
    "gateway": {
        "port": 8080,
        "agentToAgent": {
            "enabled": True,
            "comment": "Enables cross-agent messaging"
        }
    },
    "channels": {
        "feishu": {
            "accounts": {
                "orch-feishu": {
                    "appId": "cli_PLACEHOLDER_ORCH",
                    "appSecret": "PLACEHOLDER_SECRET_ORCH",
                    "agent": "orchestrator"
                },
                "contracts-feishu": {
                    "appId": "cli_PLACEHOLDER_CR",
                    "appSecret": "PLACEHOLDER_SECRET_CR",
                    "agent": "contract-reviewer"
                },
                "research-feishu": {
                    "appId": "cli_PLACEHOLDER_LR",
                    "appSecret": "PLACEHOLDER_SECRET_LR",
                    "agent": "legal-researcher"
                }
            }
        }
    },
    "bindings": [
        {
            "type": "delivery",
            "match": {"accountId": "orch-feishu"},
            "agent": "orchestrator"
        },
        {
            "type": "delivery",
            "match": {"accountId": "contracts-feishu"},
            "agent": "contract-reviewer"
        },
        {
            "type": "delivery",
            "match": {"accountId": "research-wrong-id"},
            "agent": "legal-researcher"
        }
    ],
    "agents": {
        "list": [
            {
                "id": "orchestrator",
                "workspace": "agents/orchestrator/workspace",
                "model": "gpt-4o",
                "allowAgents": ["contract-reviewer"]
            },
            {
                "id": "contract-reviewer",
                "workspace": "agents/contract-reviewer/workspace",
                "model": "gpt-4o",
                "allowAgents": []
            }
        ]
    }
}

with open(os.path.join(WORKSPACE, "openclaw.json"), "w") as f:
    json.dump(broken_config, f, indent=2)

# ── requirements brief ────────────────────────────────────────────────────────
brief = """# Legal AI Platform — Bot Integration Requirements

## Context
We are deploying four specialized AI assistants for our law firm via the internal OpenClaw platform.
Each assistant must appear as a distinct bot in Feishu (Lark) to our attorneys.

## The Four Bots

| Bot Name       | Agent ID          | Feishu App ID          | App Secret              | Role                    |
|----------------|-------------------|------------------------|-------------------------|-------------------------|
| 总调度          | orchestrator      | cli_LegalOrch001       | sOrc_X9k2mP4nQ7rT       | Orchestrates all others |
| 合同审查        | contract-reviewer | cli_ContractRev002     | sCR_Yn3vB8wL5jK1d       | Reviews contracts       |
| 法律研究        | legal-researcher  | cli_LegalRes003        | sLR_Zm6uD9xN2cH4f       | Legal research          |
| 案件管理        | case-manager      | cli_CaseMgr004         | sCM_Wq7eG1yO3iJ5g       | Case management         |

## Critical Business Requirement
The 总调度 (orchestrator) bot must be able to spawn the other three specialized bots as needed.
All three specialist bots must be spawnable by the orchestrator.

## Deliverable
Update the platform configuration so all four bots are correctly wired up and the orchestrator
can spawn the three specialists.
"""

with open(os.path.join(WORKSPACE, "requirements-brief.md"), "w") as f:
    f.write(brief)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in os.walk(WORKSPACE) for __ in _[2])}")