import os
import json
import random
import stat

random.seed(42)

workspace = "/home/agent"

# --- Create a realistic, deeply nested distractor workspace ---

# Simulate a bot development project structure
dirs = [
    "workspace/bots/sentinel",
    "workspace/bots/recon-alpha",
    "workspace/bots/legacy-crawler",
    "workspace/config_backups/2023",
    "workspace/config_backups/2024-q1",
    "workspace/logs/discovery",
    "workspace/logs/announce",
    "workspace/tools/network",
    "workspace/tools/identity",
    "workspace/docs/architecture",
    "workspace/scripts/deploy",
    "workspace/scripts/monitor",
    "workspace/tests/integration",
    "workspace/vendor/iroh-utils",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files: old/wrong configs, red herrings

# WRONG config at wrong path (distractor)
wrong_config_path = os.path.join(workspace, "workspace/config_backups/2024-q1/config.toml")
with open(wrong_config_path, "w") as f:
    f.write("""# OLD CONFIG - DO NOT USE
name = "old-bot"
announce_interval = 120
peer_ttl = 600
discover_timeout = 30
capabilities = ["legacy"]
openclaw_version = "0.9.0"
mode = "passive"
""")

# Stale peers cache (wrong location, distractor)
stale_peers_path = os.path.join(workspace, "workspace/logs/discovery/peers_snapshot.json")
with open(stale_peers_path, "w") as f:
    json.dump([
        {"node_id": "STALE_NODE_111", "name": "dead-bot", "last_seen": 1700000000, "capabilities": []},
    ], f, indent=2)

# Wrong friends file at wrong path
wrong_friends_path = os.path.join(workspace, "workspace/bots/legacy-crawler/friends.json")
with open(wrong_friends_path, "w") as f:
    json.dump([], f, indent=2)

# Distractor identity files
with open(os.path.join(workspace, "workspace/tools/identity/node_id.txt"), "w") as f:
    f.write("FAKE_NODE_ID_ABCDEF1234567890\n")

# Bot spec files (give the agent context: node IDs of friends to add)
bot_spec_path = os.path.join(workspace, "workspace/docs/architecture/fleet_manifest.json")
with open(bot_spec_path, "w") as f:
    json.dump({
        "fleet": "OpenClaw-Alpha",
        "description": "Registered companion bots for sentinel-7",
        "trusted_peers": [
            {
                "alias": "recon-alpha",
                "node_id": "b5e7f3a91c2d4e6f8a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f"
            },
            {
                "alias": "data-harvester",
                "node_id": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
            },
            {
                "alias": "watchdog-prime",
                "node_id": "f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1"
            }
        ],
        "network_params": {
            "bot_name": "sentinel-7",
            "capabilities": ["search", "monitor", "alert"],
            "announce_interval_seconds": 120,
            "peer_ttl_seconds": 600,
            "discover_timeout_seconds": 20,
            "openclaw_version": "1.0.0",
            "mode": "dedicated"
        }
    }, f, indent=2)

# Distractor scripts
with open(os.path.join(workspace, "workspace/scripts/deploy/setup_old.sh"), "w") as f:
    f.write("#!/bin/bash\n# Old setup script - deprecated\necho 'This script is no longer valid'\n")

with open(os.path.join(workspace, "workspace/scripts/monitor/health_check.sh"), "w") as f:
    f.write("#!/bin/bash\n# Check bot health\nping -c 1 localhost\n")

# Vendor readme distractors
with open(os.path.join(workspace, "workspace/vendor/iroh-utils/README.md"), "w") as f:
    f.write("# iroh-utils\nUtility wrappers for iroh QUIC connections. See main docs.\n")

# Distractor log files
for i in range(3):
    with open(os.path.join(workspace, f"workspace/logs/announce/announce_{2024+i}.log"), "w") as f:
        f.write(f"[{2024+i}] Announce log - STALE\n")
        f.write("node_id=EXPIRED_NODE_XYZ\n")

# Distractor config at a plausible but wrong path
os.makedirs(os.path.join(workspace, ".config/clawnet_old"), exist_ok=True)
with open(os.path.join(workspace, ".config/clawnet_old/config.toml"), "w") as f:
    f.write("""# Wrong subdirectory
name = "wrong-location-bot"
mode = "passive"
""")

# Recon-alpha bot notes
with open(os.path.join(workspace, "workspace/bots/recon-alpha/notes.txt"), "w") as f:
    f.write("recon-alpha: active, last contact 2024-03-15\nCapabilities: search, monitor\n")

with open(os.path.join(workspace, "workspace/bots/sentinel/deployment_notes.txt"), "w") as f:
    f.write("sentinel-7: primary coordination bot\nNeeds: search, monitor, alert capabilities\nMust register trusted fleet peers before deployment\n")

# Tests distractor
with open(os.path.join(workspace, "workspace/tests/integration/test_discovery.py"), "w") as f:
    f.write("# Integration tests for discovery - not relevant to setup\nimport unittest\n")

print("Workspace generation complete.")
print(f"Key file for agent: {bot_spec_path}")