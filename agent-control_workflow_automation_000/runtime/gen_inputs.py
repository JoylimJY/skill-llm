import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create distractor directory structure ---

# Legacy agents config dir
legacy_dir = workspace / "legacy_agents"
legacy_dir.mkdir(exist_ok=True)

(legacy_dir / "agent_manifest_v1.json").write_text(json.dumps({
    "agents": [
        {"name": "helperbot", "model": "gpt-3.5", "workspace": "/old/clawd/agents/helperbot"},
        {"name": "support-alpha", "model": "claude-2", "workspace": "/old/clawd/agents/support-alpha"},
    ]
}, indent=2))

(legacy_dir / "routing_table_2023.csv").write_text(
    "channel,agent,account\n"
    "webchat,helperbot,acct_001\n"
    "email,support-alpha,acct_002\n"
    "sms,helperbot,acct_003\n"
)

(legacy_dir / "deprecated_bindings.txt").write_text(
    "DEPRECATED: Do not use these bindings.\n"
    "webchat:acct_001 -> helperbot\n"
    "email:acct_002 -> support-alpha\n"
)

# Current ops dir
ops_dir = workspace / "ops"
ops_dir.mkdir(exist_ok=True)

(ops_dir / "channel_definitions.yaml").write_text(
    "channels:\n"
    "  - id: webchat\n"
    "    description: Primary web chat surface\n"
    "  - id: email\n"
    "    description: Email support queue\n"
    "  - id: sms\n"
    "    description: SMS short-code channel\n"
    "  - id: slack\n"
    "    description: Internal Slack workspace\n"
)

(ops_dir / "model_registry.json").write_text(json.dumps({
    "models": [
        {"id": "claw-7b-v2", "description": "Lightweight fast model"},
        {"id": "claw-70b-v1", "description": "Large high-accuracy model"},
        {"id": "claw-13b-instruct", "description": "Instruction-tuned mid model"},
    ]
}, indent=2))

(ops_dir / "oncall_notes.txt").write_text(
    "2024-06-01: helperbot causing latency spikes on webchat:acct_007. Investigate.\n"
    "2024-06-03: support-alpha decommissioned. Remove from all channels.\n"
    "2024-06-05: New agent 'nexus' to be created for premium support tier.\n"
    "            Model: claw-70b-v1, workspace: /srv/agents/nexus\n"
    "            Route to channel: email, accountId: acct_PRE_009\n"
    "            Identity: display='Nexus Support', emoji=🤖, avatar=/assets/nexus_avatar.png\n"
    "2024-06-06: Old agent 'helperbot' must be deleted after nexus is confirmed live.\n"
)

# Scripts dir (as referenced by SKILL.md)
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

(scripts_dir / "example.py").write_text(
    "# Deterministic helper wrapper for command parsing/execution\n"
    "# This script is used by the agent control skill to parse and dispatch openclaw commands.\n"
    "import subprocess\n"
    "import sys\n\n"
    "def run(cmd):\n"
    "    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)\n"
    "    print(result.stdout)\n"
    "    if result.returncode != 0:\n"
    "        print('ERROR:', result.stderr, file=sys.stderr)\n"
    "    return result.returncode\n\n"
    "if __name__ == '__main__':\n"
    "    run(' '.join(sys.argv[1:]))\n"
)

# More distractors
infra_dir = workspace / "infra" / "k8s" / "agents"
infra_dir.mkdir(parents=True, exist_ok=True)

(infra_dir / "nexus-deployment.yaml").write_text(
    "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: nexus-placeholder\n"
    "spec:\n  replicas: 0\n  # Not yet active\n"
)

(infra_dir / "helperbot-deployment.yaml").write_text(
    "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: helperbot\n"
    "spec:\n  replicas: 1\n"
)

audit_dir = workspace / "audit"
audit_dir.mkdir(exist_ok=True)

(audit_dir / "agent_change_log.csv").write_text(
    "date,action,agent,operator\n"
    "2024-05-10,create,support-alpha,ops-team\n"
    "2024-05-15,bind,support-alpha,ops-team\n"
    "2024-06-03,delete,support-alpha,ops-team\n"
)

(audit_dir / "compliance_checklist.txt").write_text(
    "[ ] Verify new agent created with correct model\n"
    "[ ] Confirm identity set before routing\n"
    "[ ] Binding audit trail updated\n"
    "[ ] Decommissioned agents deleted with confirmation\n"
)

# Ensure log file does NOT pre-exist (agent must create via openclaw calls)
log_path = workspace / "openclaw_calls.log"
if log_path.exists():
    log_path.unlink()

print("Workspace generated successfully.")
print(f"Files created under: {workspace}")