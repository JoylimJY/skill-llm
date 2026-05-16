import os
import json
import random

random.seed(42)

# ── directory scaffold ────────────────────────────────────────────────────────
home = os.path.expanduser("~")
workspace = "/workspace"

dirs = [
    f"{workspace}/agents/vector/tasks",
    f"{workspace}/agents/forge/tasks",
    f"{workspace}/agents/oracle/tasks",
    f"{workspace}/agents/shared/config",
    f"{workspace}/infra/db",
    f"{workspace}/infra/logs",
    f"{workspace}/infra/scripts",
    f"{workspace}/docs/architecture",
    f"{workspace}/docs/runbooks",
    f"{workspace}/tests/integration",
    f"{home}/.openclaw/workspace/state",
    f"{home}/.openclaw/extensions",
    f"{home}/.openclaw/logs",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ──────────────────────────────────────────────────────────
distractor_files = {
    f"{workspace}/agents/vector/tasks/task_queue.json": json.dumps({
        "tasks": [{"id": "t001", "type": "search", "priority": 1},
                  {"id": "t002", "type": "index", "priority": 2}],
        "metadata": {"version": "1.4.2"}
    }, indent=2),

    f"{workspace}/agents/forge/tasks/build_manifest.json": json.dumps({
        "builds": [{"component": "auth-service", "version": "2.1.0"},
                   {"component": "data-pipeline", "version": "1.8.3"}]
    }, indent=2),

    f"{workspace}/agents/oracle/tasks/predictions.json": json.dumps({
        "model": "ensemble-v3",
        "predictions": [{"label": "anomaly", "confidence": 0.87}]
    }, indent=2),

    f"{workspace}/agents/shared/config/routing.yaml": (
        "router:\n"
        "  strategy: round-robin\n"
        "  agents:\n"
        "    - VECTOR\n"
        "    - FORGE\n"
        "    - ORACLE\n"
        "  timeout_ms: 5000\n"
    ),

    f"{workspace}/infra/db/schema_notes.txt": (
        "Database schema notes (legacy)\n"
        "beliefs table was added in v0.3\n"
        "cosine similarity threshold: 0.92\n"
        "DO NOT DROP beliefs table manually\n"
    ),

    f"{workspace}/infra/logs/gateway.log": (
        "[2024-01-15 09:00:01] Gateway starting...\n"
        "[2024-01-15 09:00:02] Extensions loaded: 0\n"
        "[2024-01-15 09:00:03] WARN: No memory extension configured\n"
        "[2024-01-15 09:00:04] Gateway ready on port 3000\n"
    ),

    f"{workspace}/infra/scripts/deploy.sh": (
        "#!/bin/bash\n"
        "set -e\n"
        "echo 'Deploying agent platform...'\n"
        "# TODO: add memory persistence setup\n"
    ),

    f"{workspace}/docs/architecture/multi_agent_overview.md": (
        "# Multi-Agent Platform Architecture\n\n"
        "## Agents\n"
        "- **VECTOR**: Handles semantic search and retrieval\n"
        "- **FORGE**: Manages code generation and build tasks\n"
        "- **ORACLE**: Performs prediction and classification\n\n"
        "## Memory\n"
        "Each agent requires isolated persistent memory.\n"
        "Cross-contamination of beliefs between agents is NOT acceptable.\n"
        "Memory confidence threshold must be set conservatively: minimum 0.72.\n"
    ),

    f"{workspace}/docs/runbooks/memory_setup.md": (
        "# Memory Setup Runbook\n\n"
        "Status: DRAFT — incomplete\n\n"
        "## Requirements\n"
        "- VECTOR agent: max 8 core beliefs, 3 active, 3 recalled\n"
        "- FORGE agent: max 12 core beliefs, 6 active, 4 recalled\n"
        "- ORACLE agent: max 15 core beliefs, 7 active, 6 recalled\n"
        "- All agents: output chars capped at 1500, spawn budget warning at 15\n"
        "- All agents: extraction model must be the cheapest/fastest Haiku variant\n"
        "- DB path must follow the standard state directory convention\n\n"
        "## Status\n"
        "NOT YET CONFIGURED. See platform team.\n"
    ),

    f"{workspace}/tests/integration/agent_memory_test.py": (
        "import pytest\n\n"
        "def test_vector_beliefs_isolated():\n"
        "    # placeholder — requires BEE to be configured\n"
        "    pass\n\n"
        "def test_forge_beliefs_isolated():\n"
        "    pass\n\n"
        "def test_oracle_beliefs_isolated():\n"
        "    pass\n"
    ),

    f"{workspace}/infra/db/old_config_backup.json": json.dumps({
        "extensions": {
            "entries": {
                "memory_v1": {
                    "enabled": False,
                    "config": {
                        "dbPath": "/tmp/old.db",
                        "agentId": "default"
                    }
                }
            }
        }
    }, indent=2),
}

for path, content in distractor_files.items():
    with open(path, "w") as f:
        f.write(content)

# ── BROKEN / PARTIAL openclaw.json — the agent must fix and complete this ──────
# This is intentionally wrong: missing bee extension, wrong structure hints
broken_openclaw = {
    "gateway": {
        "port": 3000,
        "host": "localhost"
    },
    "extensions": {
        "entries": {
            "logger": {
                "enabled": True,
                "config": {
                    "level": "info",
                    "output": "~/.openclaw/logs/gateway.log"
                }
            }
        }
    },
    "_comment": "TODO: add memory persistence extension — see runbook"
}

openclaw_config_path = os.path.join(home, ".openclaw", "openclaw.json")
with open(openclaw_config_path, "w") as f:
    json.dump(broken_openclaw, f, indent=2)

print("Workspace initialized.")
print(f"Partial openclaw.json written to: {openclaw_config_path}")
print("Distractor files created:", len(distractor_files))