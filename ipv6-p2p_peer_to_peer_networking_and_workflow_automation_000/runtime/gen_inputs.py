import os
import json
import random

random.seed(42)

workspace = "/workspace"

# Create deeply nested directory structure with distractor files
dirs = [
    "research_ops/nodes",
    "research_ops/logs",
    "research_ops/configs",
    "network/diagnostics",
    "network/peers",
    "network/archives",
    "scripts/utils",
    "scripts/legacy",
    "data/raw",
    "data/processed",
    "skill_docs",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "research_ops/nodes/node_registry.csv": "node_id,location,status\nnode_001,EU-West,active\nnode_002,US-East,inactive\nnode_003,APAC,maintenance\n",
    "research_ops/logs/connection_log_2024.txt": "2024-01-15 10:23:11 INFO Connected to bootstrap\n2024-01-15 10:23:15 WARN Peer timeout fd77:dead::1\n2024-01-15 10:23:22 ERROR Connection refused port 8099\n",
    "research_ops/configs/legacy_config.json": json.dumps({"version": "0.0.9", "port": 8099, "peers": [], "deprecated": True}, indent=2),
    "network/diagnostics/ping_results.txt": "PING 200:abcd::1 56 bytes of data\n64 bytes from 200:abcd::1: icmp_seq=1 ttl=64 time=12.3 ms\n",
    "network/peers/known_peers_old.json": json.dumps([
        {"address": "200:aaaa::1", "alias": "OldNode", "last_seen": "2023-11-01T08:00:00Z"},
        {"address": "fd77:bbbb::2", "alias": "TestNode", "last_seen": "2023-12-15T14:30:00Z"}
    ], indent=2),
    "network/archives/peer_backup_2023.txt": "# Archived peers - DO NOT USE\n200:dead::beef - DecommissionedNode\nfd77:cafe::1 - OldTestEnv\n",
    "scripts/utils/check_ports.sh": "#!/bin/bash\n# Utility: check if a port is open\nnc -zv $1 $2 2>&1\n",
    "scripts/legacy/old_send.py": "# DEPRECATED: Use the new P2P framework instead\nimport socket\ndef send_msg(host, port, msg):\n    s = socket.socket()\n    s.connect((host, port))\n    s.send(msg.encode())\n    s.close()\n",
    "data/raw/experiment_batch_42.csv": "sample_id,measurement,timestamp\nS001,3.14159,2024-01-10T09:00:00Z\nS002,2.71828,2024-01-10T09:05:00Z\n",
    "data/processed/summary_stats.json": json.dumps({"mean": 2.929935, "std": 0.296465, "n": 2}, indent=2),
    "scripts/utils/validate_ipv6.py": "import re\ndef is_valid_ygg(addr):\n    return bool(re.match(r'^(200:|fd77:)', addr))\n",
}

for path, content in distractors.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# The SKILL.md document
skill_md = """---
name: ipv6-p2p
description: Send/receive direct encrypted P2P messages between OpenClaw agents over Yggdrasil IPv6. Handles peer discovery, messaging, and connectivity diagnostics. Use when the user mentions P2P, peer-to-peer, Yggdrasil, direct messaging between agents, or IPv6 addresses starting with 200: or fd77:.
version: 0.1.2
metadata:
  openclaw:
    emoji: "🔗"
    homepage: https://github.com/ReScienceLab/declaw
    install:
      - kind: node
        package: "@resciencelab/declaw"
---

# IPv6 P2P

Direct agent-to-agent messaging over Yggdrasil IPv6. Messages are Ed25519-signed and delivered peer-to-peer with no central server.

## Quick Reference

| Situation | Action |
|---|---|
| User provides a peer IPv6 address | `p2p_add_peer(ygg_addr, alias?)` |
| User wants to send a message | `p2p_send_message(ygg_addr, message, port?)` |
| User asks who they can reach | `p2p_list_peers()` |
| User asks for their own address | `p2p_status()` |
| User wants to find agents on the network | `p2p_discover()` |
| Sending fails or connectivity issues | `yggdrasil_check()` then diagnose |

## Tool Parameters

### p2p_add_peer
- `ygg_addr` (required): Yggdrasil `200:` or ULA `fd77:` IPv6 address
- `alias` (optional): human-readable name, e.g. "Alice"

### p2p_send_message
- `ygg_addr` (required): recipient address
- `message` (required): text content
- `port` (optional, default 8099): recipient's P2P port — pass explicitly if the peer uses a non-default port

### p2p_discover
No parameters. Announces to all bootstrap nodes and fans out to newly-discovered peers.

### p2p_status
Returns: own address, known peer count, unread inbox count.

### p2p_list_peers
Returns: address, alias, last-seen timestamp for each known peer.

## Inbound Messages

Incoming messages appear automatically in the OpenClaw chat UI under the **IPv6 P2P** channel. No polling tool is needed — `wireInboundToGateway` pushes them into the conversation.

## Error Handling

| Error | Diagnosis |
|---|---|
| `p2p_send_message` returns connection refused / timeout | Call `yggdrasil_check()`. If `derived_only` → Yggdrasil not running. If `yggdrasil` → peer is down or port blocked. |
| `p2p_discover` returns 0 new peers | Bootstrap nodes may be unreachable. Retry later or check network. |
| TOFU key mismatch (403 from peer) | Peer rotated keys. User must re-add with `p2p_add_peer`. |

## Rules

- **Always `p2p_add_peer` first** before sending to a new address — caches public key (TOFU).
- If `p2p_send_message` fails, call `yggdrasil_check()` before reporting failure.
- Never invent IPv6 addresses — always ask the user explicitly.
- Valid formats: `200:xxxx::x` (Yggdrasil mainnet) or `fd77:xxxx::x` (ULA/test).

See `references/flows.md` for example interaction patterns.
See `references/discovery.md` for how peer discovery works.
"""

with open(os.path.join(workspace, "skill_docs/SKILL.md"), "w") as f:
    f.write(skill_md)

# The mission briefing file for the agent
mission = {
    "task": "connect_and_transmit",
    "partner_institution": "Nordstern Research Institute",
    "contact_node": {
        "ipv6": "200:b33f:cafe:dead::7",
        "alias": "NordsternPrimary",
        "custom_port": 9055,
        "note": "This node runs on a non-standard port due to their firewall configuration"
    },
    "message_to_send": "Requesting access to dataset DS-2024-ARCTIC-07. Authorization code: NRSI-88421.",
    "fallback_note": "If the initial transmission fails, follow the standard diagnostic protocol before escalating.",
    "output_file": "transmission_workflow.js"
}

with open(os.path.join(workspace, "research_ops/mission_briefing.json"), "w") as f:
    json.dump(mission, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created: {len(distractors) + 2}")