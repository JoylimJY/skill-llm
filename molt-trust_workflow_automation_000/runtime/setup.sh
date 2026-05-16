#!/bin/bash
set -e

WORKSPACE="/workspace"
BIN_DIR="$WORKSPACE/.molt_bin"
LOG_DIR="$WORKSPACE/.molt_invocations"

mkdir -p "$BIN_DIR"
mkdir -p "$LOG_DIR"

# -------------------------------------------------------
# Mock: audit_agent
# -------------------------------------------------------
cat > "$BIN_DIR/audit_agent" << 'MOCK_EOF'
#!/usr/bin/env python3
import sys, json, os, datetime, hashlib

args = sys.argv[1:]
params = {}
for arg in args:
    if '=' in arg:
        k, v = arg.split('=', 1)
        params[k.strip()] = v.strip()

log_dir = "/workspace/.molt_invocations"
os.makedirs(log_dir, exist_ok=True)

entry = {
    "tool": "audit_agent",
    "params": params,
    "timestamp": datetime.datetime.utcnow().isoformat()
}

# Append to invocation log
log_file = os.path.join(log_dir, "invocations.jsonl")
with open(log_file, "a") as f:
    f.write(json.dumps(entry) + "\n")

agent_id = params.get("agentId", "unknown")
min_score = params.get("minScore", None)
strict_mode = params.get("strictMode", "false")

print(f"[molt-trust] audit_agent invoked")
print(f"  agentId    : {agent_id}")
if min_score:
    print(f"  minScore   : {min_score}")
if strict_mode == "true":
    print(f"  strictMode : {strict_mode}")
    print(f"[molt-trust] Fortress Mode: filtering to trusted_peers only")
    print(f"[molt-trust] Scanning last 10,000 blocks for agent #{agent_id}...")
    print(f"[molt-trust] Results: 2 peer-verified reviews found (minScore={min_score or 0})")
    print(f"  Avg score (peer-only): 89.5")
    print(f"  Spam filtered: 14 reviews below threshold or from untrusted wallets")
else:
    print(f"[molt-trust] Growth Mode: scanning all reviewers")
    print(f"[molt-trust] Scanning last 10,000 blocks for agent #{agent_id}...")
    print(f"[molt-trust] Results: 16 reviews found")
    print(f"  Avg score: 72.1")
MOCK_EOF

# -------------------------------------------------------
# Mock: rate_agent
# -------------------------------------------------------
cat > "$BIN_DIR/rate_agent" << 'MOCK_EOF'
#!/usr/bin/env python3
import sys, json, os, datetime

args = sys.argv[1:]
params = {}
for arg in args:
    if '=' in arg:
        k, v = arg.split('=', 1)
        params[k.strip()] = v.strip()

log_dir = "/workspace/.molt_invocations"
os.makedirs(log_dir, exist_ok=True)

entry = {
    "tool": "rate_agent",
    "params": params,
    "timestamp": datetime.datetime.utcnow().isoformat()
}

log_file = os.path.join(log_dir, "invocations.jsonl")
with open(log_file, "a") as f:
    f.write(json.dumps(entry) + "\n")

agent_id = params.get("agentId", "unknown")
score    = params.get("score", "0")
proof_tx = params.get("proofTx", None)

print(f"[molt-trust] rate_agent invoked")
print(f"  agentId : {agent_id}")
print(f"  score   : {score}")
if proof_tx:
    print(f"  proofTx : {proof_tx}")
    print(f"[molt-trust] Verified interaction proof accepted.")
else:
    print(f"[molt-trust] WARNING: No proofTx provided. Rating submitted as unverified.")
print(f"[molt-trust] Rating submitted. Estimated gas: ~0.0001 ETH")
MOCK_EOF

# -------------------------------------------------------
# Mock: manage_peers
# -------------------------------------------------------
cat > "$BIN_DIR/manage_peers" << 'MOCK_EOF'
#!/usr/bin/env python3
import sys, json, os, datetime

args = sys.argv[1:]
params = {}
for arg in args:
    if '=' in arg:
        k, v = arg.split('=', 1)
        params[k.strip()] = v.strip()

log_dir = "/workspace/.molt_invocations"
os.makedirs(log_dir, exist_ok=True)

entry = {
    "tool": "manage_peers",
    "params": params,
    "timestamp": datetime.datetime.utcnow().isoformat()
}

log_file = os.path.join(log_dir, "invocations.jsonl")
with open(log_file, "a") as f:
    f.write(json.dumps(entry) + "\n")

action = params.get("action", "unknown")
wallet = params.get("walletAddress", "unknown")

print(f"[molt-trust] manage_peers invoked")
print(f"  action        : {action}")
print(f"  walletAddress : {wallet}")
if action == "trust":
    print(f"[molt-trust] Wallet {wallet} added to trusted_peers.")
elif action == "block":
    print(f"[molt-trust] Wallet {wallet} added to blocked list.")
else:
    print(f"[molt-trust] Unknown action: {action}")
MOCK_EOF

chmod +x "$BIN_DIR/audit_agent"
chmod +x "$BIN_DIR/rate_agent"
chmod +x "$BIN_DIR/manage_peers"

# Add mock bin to PATH by creating symlinks in /usr/local/bin
ln -sf "$BIN_DIR/audit_agent"   /usr/local/bin/audit_agent
ln -sf "$BIN_DIR/rate_agent"    /usr/local/bin/rate_agent
ln -sf "$BIN_DIR/manage_peers"  /usr/local/bin/manage_peers

echo "[setup] molt-trust mock CLI tools installed and ready."
echo "[setup] Invocation logs will be written to: $LOG_DIR/invocations.jsonl"