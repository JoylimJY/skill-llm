import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create a realistic deeply nested directory structure for a fintech AI ops project
dirs = [
    "agents/data-analyst-bot/config",
    "agents/data-analyst-bot/logs",
    "agents/ops-bot/config",
    "agents/ops-bot/logs",
    "agents/audit-bot/config",
    "agents/audit-bot/logs",
    "infra/policies",
    "infra/secrets",
    "infra/monitoring",
    "scripts/deployment",
    "scripts/maintenance",
    "docs/architecture",
    "docs/runbooks",
    "tests/integration",
    "tests/unit",
    ".openclaw/plugins",
    ".openclaw/cache",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files - realistic but irrelevant to the task

# 1. Old/wrong openclaw config that must be replaced
old_config = {
    "plugins": {
        "policy-engine": {
            "enabled": False
        }
    },
    "version": "1.0"
}
with open(os.path.join(workspace, "openclaw.json.bak"), "w") as f:
    json.dump(old_config, f, indent=2)

# 2. Agent-specific config files (distractors)
analyst_config = {
    "agent_id": "data-analyst-bot",
    "model": "anthropic/claude-opus-4",
    "tools": ["read", "web_search", "web_fetch", "memory_search"],
    "description": "Read-only data analysis agent"
}
with open(os.path.join(workspace, "agents/data-analyst-bot/config/agent.json"), "w") as f:
    json.dump(analyst_config, f, indent=2)

ops_config = {
    "agent_id": "ops-bot",
    "model": "anthropic/claude-opus-4",
    "tools": ["exec", "process", "write", "read", "message"],
    "description": "Operations agent with exec capabilities",
    "custom_tools": ["deploy_hook"]
}
with open(os.path.join(workspace, "agents/ops-bot/config/agent.json"), "w") as f:
    json.dump(ops_config, f, indent=2)

audit_config = {
    "agent_id": "audit-bot",
    "model": "ollama/qwen2.5:latest",
    "tools": ["read", "memory_search", "memory_get", "message"],
    "description": "Audit agent - strictly read-only"
}
with open(os.path.join(workspace, "agents/audit-bot/config/agent.json"), "w") as f:
    json.dump(audit_config, f, indent=2)

# 3. Security requirements document (the actual business requirements)
requirements = """# Fintech AI Governance Requirements
# DO NOT USE THIS FILE AS CONFIG - This is a requirements specification only

## Agent Profiles

### data-analyst-bot
- Agent ID: data-analyst-bot
- Allowed tools: read, web_fetch, web_search, memory_search, message
- Profile name: analyst

### ops-bot
- Agent ID: ops-bot
- Allowed tools: read, write, edit, exec, process, message
- Profile name: ops-engineer
- IMPORTANT: The custom tool 'deploy_hook' must be treated as highest risk (T2 equivalent)
- IMPORTANT: gateway tool must always be accessible (anti-deadlock requirement)

### audit-bot
- Agent ID: audit-bot
- Allowed tools: read, memory_search, memory_get, session_status, message
- Profile name: auditor

## Security Rules

### Blocked Operations (exec tool only)
- Pattern 1: npm publish commands
- Pattern 2: docker push commands
- Pattern 3: curl or wget piped to bash/sh (pipe-to-shell attacks)
- Pattern 4: Fork bomb pattern: :(){ :|:& };:

### File Write Restrictions
- Write operations only allowed under: /opt/fintech/workspace
- Edit operations only allowed under: /opt/fintech/workspace

## Operational Settings
- Max blocked retries before escalation: 5 (not the default)
- Enable safe testing mode (log only, do not block) for initial rollout
- In safe testing mode, read-only (T0) tools should still be fully allowed
- Plugin must be active/enabled

## Anti-deadlock Requirements
- Essential communication and control tools must NEVER be blocked regardless of other rules
- This includes gateway, session management, and user messaging tools
"""

with open(os.path.join(workspace, "infra/policies/governance-requirements.txt"), "w") as f:
    f.write(requirements)

# 4. Partial/incorrect policy attempt (distractor - wrong structure)
wrong_attempt = {
    "policy-engine": {
        "allowlists": {
            "analyst": ["read", "web_fetch"],
        },
        "deny": ["npm publish", "docker push"]
    }
}
with open(os.path.join(workspace, "infra/policies/policy-attempt.json"), "w") as f:
    json.dump(wrong_attempt, f, indent=2)

# 5. Various distractor files
with open(os.path.join(workspace, "scripts/deployment/deploy.sh"), "w") as f:
    f.write("#!/bin/bash\n# Deployment script\necho 'Deploying...'\nnpm publish\ndocker push myrepo/image:latest\n")

with open(os.path.join(workspace, "scripts/maintenance/cleanup.sh"), "w") as f:
    f.write("#!/bin/bash\n# Maintenance script\nrm -rf /tmp/cache\n")

with open(os.path.join(workspace, "docs/architecture/overview.md"), "w") as f:
    f.write("# Architecture Overview\n\nThe fintech AI system uses multiple specialized agents...\n")

with open(os.path.join(workspace, "docs/runbooks/incident-response.md"), "w") as f:
    f.write("# Incident Response\n\nIn case of policy violation...\n")

# 6. Fake logs (distractors)
for i in range(5):
    with open(os.path.join(workspace, f"agents/ops-bot/logs/session_{1000+i}.log"), "w") as f:
        f.write(f"[2026-02-{7+i:02d}] Session started\n[2026-02-{7+i:02d}] exec: npm install\n[2026-02-{7+i:02d}] Session ended\n")

# 7. Plugin cache distractor
with open(os.path.join(workspace, ".openclaw/plugins/registry.json"), "w") as f:
    json.dump({"installed": ["policy-engine@1.1.0", "web-tools@2.3.1"]}, f, indent=2)

# 8. Tests distractor
with open(os.path.join(workspace, "tests/integration/test_agents.py"), "w") as f:
    f.write("# Integration tests for agent workflows\nimport pytest\n\ndef test_analyst_readonly():\n    pass\n")

# 9. Monitoring config distractor
with open(os.path.join(workspace, "infra/monitoring/alerts.yaml"), "w") as f:
    f.write("alerts:\n  - name: policy_violation\n    threshold: 10\n    window: 5m\n")

# 10. A note about what file needs to be created
with open(os.path.join(workspace, "TASK.md"), "w") as f:
    f.write("""# Task

Configure the OpenClaw policy engine for our three-agent fintech system.

See infra/policies/governance-requirements.txt for the requirements.

The final configuration must be placed in the workspace root as: openclaw.json

Consult the policy engine documentation (SKILL.md) for the correct configuration format and schema.
""")

print("Workspace initialized successfully.")
print(f"Structure created with {len(dirs)} directories and multiple distractor files.")