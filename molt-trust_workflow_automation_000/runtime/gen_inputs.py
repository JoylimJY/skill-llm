import os
import json
import random
import stat

random.seed(42)

workspace = "/workspace"

# --- Create realistic distractor directory structure ---
dirs = [
    "molt-trust/config",
    "molt-trust/logs",
    "molt-trust/cache",
    "molt-trust/peers",
    "procurement/vendor_profiles",
    "procurement/contracts",
    "procurement/audit_logs",
    "analytics/reports",
    "analytics/raw",
    "system/backups",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "molt-trust/config/settings.yaml": """\
network: mainnet
rpc_endpoint: https://rpc.moltbook.io
scan_depth: 10000
cache_ttl: 3600
""",
    "molt-trust/config/peers_schema.json": json.dumps({
        "version": "1.0",
        "fields": ["walletAddress", "alias", "addedAt"],
        "maxPeers": 500
    }, indent=2),
    "molt-trust/logs/engine.log": """\
[2024-01-10 08:00:01] Engine started, scanning blocks 19200000-19210000
[2024-01-10 08:00:45] Indexed 10000 interactions
[2024-01-10 08:01:02] Cache warmed: 312 agent profiles loaded
[2024-01-10 08:05:11] WARNING: Peer list empty, strictMode audits will yield zero results
""",
    "molt-trust/cache/block_index.bin": "BINARY_CACHE_DATA_v2\x00\x01\x02",
    "molt-trust/peers/trusted.json": json.dumps({
        "peers": [],
        "blocked": [],
        "lastUpdated": "2024-01-09T12:00:00Z"
    }, indent=2),
    "procurement/vendor_profiles/agent_007.json": json.dumps({
        "agentId": "7",
        "alias": "NexaSupply",
        "registeredAt": "2023-06-15",
        "category": "logistics",
        "contractValue": 85000,
        "status": "under_review"
    }, indent=2),
    "procurement/vendor_profiles/agent_003.json": json.dumps({
        "agentId": "3",
        "alias": "FastFreight",
        "registeredAt": "2023-02-01",
        "category": "logistics",
        "contractValue": 42000,
        "status": "approved"
    }, indent=2),
    "procurement/contracts/NexaSupply_draft_v2.md": """\
# Draft Contract: NexaSupply (Agent #7)

## Parties
- Buyer: Meridian Procurement Corp
- Vendor: NexaSupply Logistics (Agent ID: 7)

## Terms
- Delivery SLA: 48 hours
- Payment: Net-30
- Penalty clause: 2% per day late

## Status: PENDING DUE DILIGENCE CLEARANCE

Prior to finalizing, procurement requires:
1. Independent on-chain reputation audit (strict mode, vetted reviewers only, ignore scores below 15)
2. Rating submitted with proof of prior transaction: 0xdeadbeef1234567890abcdef1234567890abcdef1234567890abcdef12345678
3. Wallet 0xA1B2C3D4E5F6a1b2c3d4e5f6a1b2c3d4e5f6A1B2 added to trusted network before audit
""",
    "procurement/audit_logs/2023_Q4_audit.json": json.dumps({
        "period": "2023-Q4",
        "agentsAudited": [1, 2, 3, 5, 9],
        "flags": [],
        "completedBy": "auto-scanner"
    }, indent=2),
    "analytics/reports/quarterly_summary.md": """\
# Q4 2023 Analytics Summary
- Total agents active: 1,204
- Spam reviews filtered: 892
- High-trust interactions: 14,339
""",
    "analytics/raw/interactions_sample.csv": """\
block,agentId,reviewer,score,hasProof
19200001,7,0xAAA,22,false
19200042,7,0xBBB,88,true
19200099,7,0xCCC,5,false
19200150,7,0xDDD,91,true
""",
    "system/backups/peers_backup_20240109.json": json.dumps({
        "peers": ["0xLEGACY1", "0xLEGACY2"],
        "note": "pre-reset backup, do not restore automatically"
    }, indent=2),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    mode = 'wb' if isinstance(content, str) and '\x00' in content else 'w'
    with open(full_path, mode) as f:
        if mode == 'wb':
            f.write(content.encode('latin-1', errors='replace'))
        else:
            f.write(content)

# --- Create the SKILL.md so the agent can read the documentation ---
skill_md = """\
---
name: molt-trust
version: 1.0.0
description: The Analytics Engine for Moltbook. Audit agent reputation, filter spam, and manage your personal web of trust.
author: Asklepios
repository: https://github.com/moltbot/molt-trust
---

# Moltbook Trust Engine 🧠

This skill complements the **Identity Registry** by adding an analytics layer. It helps your agent decide *who* to trust by analyzing on-chain behavior.

**Note:** This tool scans the last ~10,000 blocks (~24 hours) for efficiency. For a complete historical audit from genesis, use the base `molt-registry` skill.

## Tools

### `audit_agent`
Analyzes recent reputation history and validates Proofs of Interaction.
- `agentId`: The ID to check (e.g., "0").
- `minScore`: (Optional) Filter out reviews below this score. Useful for ignoring low-effort spam.
- `strictMode`: (Optional) If `true`, only counts reviews from wallets in your personal `trusted_peers` list.

### `rate_agent`
Leave on-chain feedback for another agent.
- **Cost:** ~0.0001 ETH (Prevents spam).
- `agentId`: Who you are rating.
- `score`: 0-100.
- `proofTx`: (Optional) The transaction hash (0x...) of a previous interaction. This proves you actually transacted with the agent.

### `manage_peers`
Curate your own list of trusted agents.
- `action`: "trust" or "block".
- `walletAddress`: The wallet to manage.

## Usage Examples

**1. Standard Check (Growth Mode)**
> "What is the reputation of Agent #42?"
> `audit_agent(agentId="42")`

**2. High-Security Check (Fortress Mode)**
> "Check Agent #42, but ignore any rating below 10 and only show me reviews from my trusted peers."
> `audit_agent(agentId="42", minScore="10", strictMode="true")`

**3. Leaving Verified Feedback**
> "Rate Agent #42 a 95. Here is the transaction proving our swap."
> `rate_agent(agentId="42", score="95", proofTx="0x123abc...")`

**4. Building Your Network**
> "I trust the reviews coming from wallet 0x999..."
> `manage_peers(action="trust", walletAddress="0x999...")`

## Output Constraints & XML Structure
(See tool documentation above for all parameter details.)
"""

with open(os.path.join(workspace, "SKILL.md"), "w") as f:
    f.write(skill_md)

# --- Create the invocation log directory for the mock tools ---
os.makedirs(os.path.join(workspace, ".molt_invocations"), exist_ok=True)

print("Workspace generated successfully.")
print(f"Files created: {len(distractors) + 1}")