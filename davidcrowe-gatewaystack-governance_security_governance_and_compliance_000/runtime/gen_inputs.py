import os
import json
import random
import pathlib
import shutil

random.seed(42)

HOME = pathlib.Path(os.path.expanduser("~"))
WORKSPACE = pathlib.Path("/home/agentuser/workspace")
WORKSPACE.mkdir(parents=True, exist_ok=True)

# ── 1. Simulate the OpenClaw plugin directory structure ──────────────────────
PLUGIN_DIR = HOME / ".openclaw" / "plugins" / "gatewaystack-governance"
PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

# policy.example.json — the canonical template the agent must copy & modify
policy_example = {
    "version": "1.0",
    "identity": {
        "enabled": True,
        "agents": {
            "_comment": "Map agent IDs to policy roles. Unknown agents are denied.",
            "example-agent-001": "reader",
            "example-agent-002": "writer"
        },
        "roles": {
            "reader": { "description": "Read-only operations" },
            "writer": { "description": "Read-write operations" }
        }
    },
    "scope": {
        "enabled": True,
        "_comment": "Deny-by-default. Only listed tools are permitted.",
        "allowlist": {
            "reader": ["tool.read_file", "tool.list_dir"],
            "writer": ["tool.read_file", "tool.write_file", "tool.list_dir"]
        }
    },
    "rate_limiting": {
        "enabled": True,
        "per_user": {
            "window_seconds": 60,
            "max_calls": 100
        },
        "per_session": {
            "window_seconds": 3600,
            "max_calls": 1000
        }
    },
    "injection_detection": {
        "enabled": True,
        "sensitivity": "medium",
        "action": "block"
    },
    "audit_logging": {
        "enabled": True,
        "path": "~/.openclaw/logs/audit.jsonl",
        "append_only": True
    },
    "dlp": {
        "enabled": False,
        "_comment": "Requires @gatewaystack/transformabl-core. Options: 'log' or 'redact'",
        "mode": "log",
        "patterns": ["default"]
    },
    "escalation": {
        "enabled": False,
        "_comment": "Human-in-the-loop review for medium-severity detections and first-time tool use."
    },
    "behavioral_monitoring": {
        "enabled": False,
        "_comment": "Requires @gatewaystack/limitabl-core. Detects anomalous tool usage patterns."
    }
}

with open(PLUGIN_DIR / "policy.example.json", "w") as f:
    json.dump(policy_example, f, indent=2)

# ── 2. Other plugin directories (distractors) ───────────────────────────────
for plugin_name in ["openclaw-memory", "openclaw-tools-fs", "openclaw-tools-http", "openclaw-summarizer"]:
    d = HOME / ".openclaw" / "plugins" / plugin_name
    d.mkdir(parents=True, exist_ok=True)
    fake_manifest = {
        "name": plugin_name,
        "version": "0.3." + str(random.randint(1, 9)),
        "description": f"Plugin: {plugin_name}",
        "enabled": True
    }
    with open(d / "manifest.json", "w") as f:
        json.dump(fake_manifest, f, indent=2)
    with open(d / "index.js", "w") as f:
        f.write(f"// {plugin_name} entry point\nmodule.exports = {{}};\n")

# ── 3. OpenClaw main config (distractor) ─────────────────────────────────────
openclaw_conf_dir = HOME / ".openclaw"
main_config = {
    "version": "2.1.0",
    "default_model": "gpt-4o",
    "plugins_dir": "~/.openclaw/plugins",
    "log_level": "info",
    "telemetry": False
}
with open(openclaw_conf_dir / "config.json", "w") as f:
    json.dump(main_config, f, indent=2)

# ── 4. Logs directory and stale audit file (distractor) ─────────────────────
logs_dir = openclaw_conf_dir / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
stale_entries = []
for i in range(5):
    stale_entries.append(json.dumps({
        "ts": f"2024-0{i+1}-15T10:23:00Z",
        "agent": "example-agent-001",
        "tool": "tool.read_file",
        "decision": "allow",
        "check": "scope"
    }))
with open(logs_dir / "audit.jsonl", "w") as f:
    f.write("\n".join(stale_entries) + "\n")

# ── 5. Workspace distractor files ────────────────────────────────────────────
subdirs = [
    WORKSPACE / "compliance" / "reports",
    WORKSPACE / "compliance" / "drafts",
    WORKSPACE / "agents" / "trading-bot",
    WORKSPACE / "agents" / "risk-analyzer",
    WORKSPACE / "agents" / "portfolio-manager",
    WORKSPACE / "infra" / "k8s",
    WORKSPACE / "infra" / "terraform",
    WORKSPACE / "docs",
    WORKSPACE / "scripts",
]
for d in subdirs:
    d.mkdir(parents=True, exist_ok=True)

# Distractor: incomplete/stale policy attempt (wrong location, wrong content)
stale_policy = {
    "note": "DRAFT - do not use",
    "tools_allowed": ["*"],
    "dlp": False
}
with open(WORKSPACE / "compliance" / "drafts" / "policy_draft.json", "w") as f:
    json.dump(stale_policy, f, indent=2)

# Distractor: agent manifest files
for agent_id, role in [("trading-bot-alpha", "executor"), ("risk-analyzer-v2", "auditor"), ("portfolio-manager-001", "reader")]:
    manifest = {
        "agent_id": agent_id,
        "role": role,
        "tools": ["tool.market_data", "tool.place_order", "tool.read_portfolio"],
        "owner": "fintech-platform-team"
    }
    agent_dir = WORKSPACE / "agents" / agent_id.split("-")[0] + "-" + agent_id.split("-")[1]
    agent_dir = WORKSPACE / "agents" / agent_id.rsplit("-", 1)[0]
    agent_dir.mkdir(parents=True, exist_ok=True)
    with open(agent_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

# Distractor: README-like business requirements doc (no technical hints)
requirements = """# Fintech AI Platform — Governance Requirements

## Compliance Mandate (Q3 2025)

The following agents must be onboarded into the governance system:

- trading-bot-alpha   (role: executor)
- risk-analyzer-v2    (role: auditor)

Permitted tools per role:
  executor: tool.market_data, tool.place_order, tool.execute_trade
  auditor:  tool.market_data, tool.read_audit_log, tool.generate_report

Security requirements:
  - Any PII or account numbers in tool outputs must be REDACTED (not just logged)
  - Unusual or anomalous tool-call sequences must be flagged automatically
  - Rate limit: max 30 calls per 60-second window per user

All other settings should remain at their defaults unless compliance requires otherwise.
"""
with open(WORKSPACE / "docs" / "governance_requirements.md", "w") as f:
    f.write(requirements)

# Distractor: k8s and terraform stubs
with open(WORKSPACE / "infra" / "k8s" / "deployment.yaml", "w") as f:
    f.write("apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: trading-bot-alpha\n")
with open(WORKSPACE / "infra" / "terraform" / "main.tf", "w") as f:
    f.write('provider "aws" { region = "us-east-1" }\n')

# Distractor: npm package.json in workspace (not the right place for governance packages)
pkg = {
    "name": "fintech-platform",
    "version": "1.0.0",
    "description": "Fintech AI platform services",
    "dependencies": {
        "express": "^4.18.2",
        "lodash": "^4.17.21"
    }
}
with open(WORKSPACE / "package.json", "w") as f:
    json.dump(pkg, f, indent=2)

# Distractor: scripts
with open(WORKSPACE / "scripts" / "deploy.sh", "w") as f:
    f.write("#!/bin/bash\necho 'Deploying fintech platform...'\n")
with open(WORKSPACE / "scripts" / "health_check.sh", "w") as f:
    f.write("#!/bin/bash\ncurl -s http://localhost:8080/health\n")

print("Workspace and plugin skeleton generated successfully.")
print(f"Plugin dir: {PLUGIN_DIR}")
print(f"policy.example.json created: {(PLUGIN_DIR / 'policy.example.json').exists()}")
print(f"policy.json exists (should be False): {(PLUGIN_DIR / 'policy.json').exists()}")