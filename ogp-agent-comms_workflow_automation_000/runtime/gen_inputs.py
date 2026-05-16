import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create a realistic distractor directory structure simulating a research team's project
dirs = [
    "research/memory-systems/v1",
    "research/memory-systems/v2",
    "research/testing-framework/unit",
    "research/testing-framework/integration",
    "federation/peers/archive",
    "federation/scopes",
    "logs/activity/2026-03",
    "logs/activity/2026-04",
    "config/backups",
    "config/templates",
    "scripts/maintenance",
    "docs/api",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "research/memory-systems/v1/architecture.md": "# Memory System Architecture v1\nOld design document...",
    "research/memory-systems/v2/architecture.md": "# Memory System Architecture v2\nUpdated with peer caching layer.",
    "research/testing-framework/unit/test_runner.py": "import pytest\n# placeholder test runner\ndef test_placeholder():\n    assert True\n",
    "research/testing-framework/integration/run_tests.sh": "#!/bin/bash\necho 'Running integration tests...'\n",
    "federation/peers/archive/old_peers.json": json.dumps([
        {"id": "deadbeef12345678", "displayName": "OldBot", "status": "revoked"},
        {"id": "cafebabe87654321", "displayName": "DeprecatedAgent", "status": "revoked"}
    ], indent=2),
    "federation/scopes/scope_grants.json": json.dumps({
        "a1b2c3d4e5f6a1b2": ["memory-management", "testing", "general", "code-review"],
        "9f8e7d6c5b4a9f8e": ["general", "status-updates"]
    }, indent=2),
    "logs/activity/2026-03/march_summary.log": "2026-03-15 09:00:00 [IN]  ResearchBot-Alpha → testing: Ping test\n2026-03-15 09:00:01 [OUT] → ResearchBot-Alpha: Pong\n",
    "logs/activity/2026-04/april_summary.log": "2026-04-01 10:00:00 [IN]  DataBot-Beta → general: Hello\n2026-04-01 10:00:01 [OUT] → DataBot-Beta: Hi\n",
    "config/backups/peers_backup_20260301.json": json.dumps([
        {"id": "a1b2c3d4e5f6a1b2", "displayName": "ResearchBot-Alpha", "responsePolicy": {}},
        {"id": "9f8e7d6c5b4a9f8e", "displayName": "DataBot-Beta", "responsePolicy": {}}
    ], indent=2),
    "config/templates/policy_template.json": json.dumps({
        "responsePolicy": {
            "TOPIC_NAME": {
                "level": "LEVEL_HERE",
                "notes": "NOTES_HERE"
            }
        }
    }, indent=2),
    "scripts/maintenance/cleanup_logs.sh": "#!/bin/bash\nfind /workspace/logs -name '*.log' -mtime +30 -delete\n",
    "docs/api/federation_api.md": "# Federation API\nEndpoints for managing peer relationships.\n## GET /peers\nReturns list of all peers.\n",
}

for filepath, content in distractors.items():
    full_path = workspace / filepath
    full_path.write_text(content)

# Create a MESSY/INCOMPLETE ogp config directory simulating a partially initialized setup
# The agent will need to run ogp commands to properly configure it
ogp_dir = Path.home() / ".ogp"
ogp_dir.mkdir(exist_ok=True)

# Pre-populate peers.json with approved peers but NO response policies yet
# This simulates peers already federated but not yet configured for agent-comms
peers_data = [
    {
        "id": "a1b2c3d4e5f6a1b2",
        "displayName": "ResearchBot-Alpha",
        "status": "approved",
        "publicKey": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        "federatedAt": "2026-03-01T10:00:00Z"
    },
    {
        "id": "9f8e7d6c5b4a9f8e",
        "displayName": "DataBot-Beta",
        "status": "approved",
        "publicKey": "9f8e7d6c5b4a9f8e7d6c5b4a9f8e7d6c",
        "federatedAt": "2026-03-15T14:00:00Z"
    },
    {
        "id": "deadbeef12345678",
        "displayName": "OldBot",
        "status": "revoked",
        "publicKey": "deadbeef12345678deadbeef12345678",
        "federatedAt": "2025-12-01T08:00:00Z"
    }
]
(ogp_dir / "peers.json").write_text(json.dumps(peers_data, indent=2))

# Create a partial/incomplete config.json - missing agentComms section entirely
# This is the "messy" state the agent must fix
partial_config = {
    "version": "0.2.24",
    "daemon": {
        "port": 8765,
        "host": "localhost"
    },
    "identity": {
        "displayName": "MyResearchAgent",
        "keyFile": "~/.ogp/identity.key"
    }
    # NOTE: agentComms section is intentionally MISSING
}
(ogp_dir / "config.json").write_text(json.dumps(partial_config, indent=2))

# Create a misleading "notes.txt" in workspace root that has wrong syntax
(workspace / "communication_policy_draft.txt").write_text(
    "DRAFT POLICY NOTES (NOT FINAL)\n"
    "=================================\n"
    "ResearchBot-Alpha: should handle memory-management and testing at full level\n"
    "DataBot-Beta: general comms only, high-level summaries\n"
    "Global: everyone gets summary level for general topics\n"
    "\n"
    "TODO: Also add code-review topic for Alpha but only escalate (check with human)\n"
    "\n"
    "NOTE: These are rough notes - need to be properly configured!\n"
    "Wrong command format attempt: ogp configure-comms alpha full-access\n"
)

print("Workspace and OGP pre-config generated successfully.")
print(f"OGP dir: {ogp_dir}")
print(f"Workspace: {workspace}")