#!/bin/bash
set -e

# ============================================================
# Create a mock `neo-market` binary that simulates the CLI
# with realistic, stateful behavior persisted to a state file.
# ============================================================

STATE_FILE="/tmp/neo_market_state.json"
CALL_LOG="/tmp/neo_market_calls.jsonl"

# Initialize state
cat > "$STATE_FILE" <<'EOF'
{
  "registered": false,
  "manifest": null,
  "bids": [],
  "deliveries": [],
  "jobs": [
    {
      "id": 1,
      "title": "Smart Contract Security Audit",
      "buyer": "0xBuyer001",
      "budget": 1200,
      "status": "Assigned",
      "deadline": "2025-08-01T00:00:00Z",
      "description": "Audit a DeFi protocol for vulnerabilities.",
      "escrow_id": 3
    },
    {
      "id": 2,
      "title": "On-Chain Data Analysis & Clustering Report",
      "buyer": "0xBuyer002",
      "budget": 400,
      "status": "Open",
      "deadline": "2025-08-15T00:00:00Z",
      "description": "Analyze 6 months of DEX trading data, identify clusters, deliver a report.",
      "escrow_id": null
    },
    {
      "id": 3,
      "title": "NFT Metadata Generation",
      "buyer": "0xBuyer003",
      "budget": 200,
      "status": "Completed",
      "deadline": "2025-07-20T00:00:00Z",
      "description": "Generate metadata for 10k NFT collection.",
      "escrow_id": 11
    },
    {
      "id": 4,
      "title": "Whitepaper Summarization",
      "buyer": "0xBuyer004",
      "budget": 150,
      "status": "Cancelled",
      "deadline": "2025-07-25T00:00:00Z",
      "description": "Summarize 5 DeFi whitepapers.",
      "escrow_id": null
    },
    {
      "id": 5,
      "title": "Price Feed Oracle Integration",
      "buyer": "0xBuyer005",
      "budget": 800,
      "status": "Expired",
      "deadline": "2025-07-01T00:00:00Z",
      "description": "Integrate Chainlink price feeds into an existing contract.",
      "escrow_id": null
    }
  ]
}
EOF

# Create the mock neo-market binary
cat > /usr/local/bin/neo-market <<'SCRIPT'
#!/usr/bin/env python3
import sys
import json
import os
import datetime
import re

STATE_FILE = "/tmp/neo_market_state.json"
CALL_LOG = "/tmp/neo_market_calls.jsonl"

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def log_call(cmd, args, result):
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "command": cmd,
        "args": args,
        "result": result
    }
    with open(CALL_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def parse_args(argv):
    """Simple flag parser: --key value -> {key: value}"""
    result = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith("--"):
            key = argv[i][2:]
            if i + 1 < len(argv) and not argv[i+1].startswith("--"):
                result[key] = argv[i+1]
                i += 2
            else:
                result[key] = True
                i += 1
        else:
            i += 1
    return result

args = sys.argv[1:]
if not args:
    print("Usage: neo-market <command> [options]")
    print("Commands: register, jobs, bid, deliver")
    sys.exit(1)

command = args[0]
flags = parse_args(args[1:])

state = load_state()

# ---- REGISTER ----
if command == "register":
    manifest = flags.get("manifest", "")
    if not manifest:
        print("Error: --manifest is required")
        log_call(command, flags, "error: missing manifest")
        sys.exit(1)
    if not manifest.startswith("ipfs://"):
        print("Error: manifest must be an IPFS URI (ipfs://Qm...)")
        log_call(command, flags, "error: invalid manifest format")
        sys.exit(1)
    state["registered"] = True
    state["manifest"] = manifest
    save_state(state)
    print(f"✅ Identity registered on-chain.")
    print(f"   Manifest: {manifest}")
    print(f"   Tx: 0x{'a1b2c3d4' * 8}")
    log_call(command, flags, "success")

# ---- JOBS ----
elif command == "jobs":
    limit = int(flags.get("limit", 10))
    jobs = state["jobs"][:limit]
    print(f"{'='*60}")
    print(f"  NEO MARKET — Available Jobs")
    print(f"{'='*60}")
    status_icons = {
        "Open": "🟢",
        "Assigned": "🔄",
        "Completed": "✅",
        "Cancelled": "🚫",
        "Expired": "⚠️"
    }
    for job in jobs:
        icon = status_icons.get(job["status"], "❓")
        print(f"\nJob #{job['id']:>3}  {icon} Status: {job['status']}")
        print(f"  Title:    {job['title']}")
        print(f"  Budget:   {job['budget']} USDC")
        print(f"  Deadline: {job['deadline']}")
        print(f"  Buyer:    {job['buyer']}")
        print(f"  Desc:     {job['description']}")
        if job.get("escrow_id"):
            print(f"  Escrow:   #{job['escrow_id']}")
    print(f"\n{'='*60}")
    print(f"Showing {len(jobs)} jobs. Use --limit N for more.")
    log_call(command, flags, f"listed {len(jobs)} jobs")

# ---- BID ----
elif command == "bid":
    if not state.get("registered"):
        print("Error: You must register first (neo-market register --manifest ipfs://...)")
        log_call(command, flags, "error: not registered")
        sys.exit(1)

    job_id_str = flags.get("job")
    price_str = flags.get("price")
    eta_str = flags.get("eta")
    cid = flags.get("cid", "")

    if not all([job_id_str, price_str, eta_str, cid]):
        print("Error: --job, --price, --eta, and --cid are all required")
        log_call(command, flags, "error: missing params")
        sys.exit(1)

    try:
        job_id = int(job_id_str)
        price = float(price_str)
        eta = int(eta_str)
    except ValueError:
        print("Error: --job and --eta must be integers, --price must be a number")
        log_call(command, flags, "error: invalid param types")
        sys.exit(1)

    if not cid.startswith("ipfs://"):
        print("Error: --cid must be a valid IPFS URI (e.g., ipfs://QmYourCID)")
        log_call(command, flags, "error: invalid cid format")
        sys.exit(1)

    # Find job
    job = next((j for j in state["jobs"] if j["id"] == job_id), None)
    if not job:
        print(f"Error: Job #{job_id} not found")
        log_call(command, flags, f"error: job {job_id} not found")
        sys.exit(1)

    if job["status"] != "Open":
        print(f"Error: Job #{job_id} is not Open (Status: {job['status']}). Cannot bid.")
        log_call(command, flags, f"error: job {job_id} not open")
        sys.exit(1)

    if price > job["budget"]:
        print(f"Warning: Your price ({price} USDC) exceeds the buyer's budget ({job['budget']} USDC). Bid may be rejected.")

    # Create bid and simulate selection (for job 2, assign escrow 7)
    escrow_id = 7 if job_id == 2 else (job_id * 3)
    bid_record = {
        "job_id": job_id,
        "price": price,
        "eta": eta,
        "cid": cid,
        "escrow_id": escrow_id,
        "status": "placed"
    }
    state["bids"].append(bid_record)
    # Update job status
    for j in state["jobs"]:
        if j["id"] == job_id:
            j["status"] = "Assigned"
            j["escrow_id"] = escrow_id
    save_state(state)

    print(f"✅ Bid placed successfully on Job #{job_id}!")
    print(f"   Price:    {price} USDC")
    print(f"   ETA:      {eta} seconds")
    print(f"   Proposal: {cid}")
    print(f"   Bid Tx:   0x{'b2c3d4e5' * 8}")
    print(f"")
    print(f"⏳ Waiting for buyer selection...")
    print(f"🔔 You were selected! Escrow locked.")
    print(f"   Escrow ID: {escrow_id}")
    print(f"   Status: Assigned — complete the work and call 'deliver'")
    log_call(command, flags, f"success: bid placed, escrow={escrow_id}")

# ---- DELIVER ----
elif command == "deliver":
    job_id_str = flags.get("job")
    escrow_id_str = flags.get("escrow")
    cid = flags.get("cid", "")

    if not all([job_id_str, escrow_id_str, cid]):
        print("Error: --job, --escrow, and --cid are all required")
        log_call(command, flags, "error: missing params")
        sys.exit(1)

    try:
        job_id = int(job_id_str)
        escrow_id = int(escrow_id_str)
    except ValueError:
        print("Error: --job and --escrow must be integers")
        log_call(command, flags, "error: invalid param types")
        sys.exit(1)

    if not cid.startswith("ipfs://"):
        print("Error: --cid must be a valid IPFS URI")
        log_call(command, flags, "error: invalid cid format")
        sys.exit(1)

    # Find job
    job = next((j for j in state["jobs"] if j["id"] == job_id), None)
    if not job:
        print(f"Error: Job #{job_id} not found")
        log_call(command, flags, f"error: job {job_id} not found")
        sys.exit(1)

    if job["status"] != "Assigned":
        print(f"Error: Job #{job_id} is not in Assigned state (Status: {job['status']})")
        log_call(command, flags, f"error: job {job_id} not assigned")
        sys.exit(1)

    if job.get("escrow_id") != escrow_id:
        print(f"Error: Escrow ID mismatch. Expected #{job['escrow_id']}, got #{escrow_id}")
        log_call(command, flags, f"error: escrow mismatch expected={job['escrow_id']} got={escrow_id}")
        sys.exit(1)

    # Record delivery
    delivery = {
        "job_id": job_id,
        "escrow_id": escrow_id,
        "cid": cid,
        "delivered_at": datetime.datetime.utcnow().isoformat() + "Z"
    }
    state["deliveries"].append(delivery)
    for j in state["jobs"]:
        if j["id"] == job_id:
            j["status"] = "Completed"
    save_state(state)

    print(f"✅ Work delivered successfully for Job #{job_id}!")
    print(f"   Result CID: {cid}")
    print(f"   Escrow #{escrow_id} released.")
    print(f"   Deliver Tx: 0x{'c3d4e5f6' * 8}")
    print(f"💸 Payment of {next((b['price'] for b in state['bids'] if b['job_id']==job_id), 0)} USDC released to your wallet.")
    log_call(command, flags, f"success: delivered job={job_id} escrow={escrow_id} cid={cid}")

else:
    print(f"Unknown command: {command}")
    print("Commands: register, jobs, bid, deliver")
    sys.exit(1)

SCRIPT

chmod +x /usr/local/bin/neo-market

# Initialize the call log
touch /tmp/neo_market_calls.jsonl

# Set up environment variables for the agent (dummy private key)
cat >> /etc/environment <<'EOF'
PRIVATE_KEY=0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef
BASE_RPC_URL=https://ethereum-sepolia-rpc.publicnode.com
EOF

echo "Mock neo-market CLI installed at /usr/local/bin/neo-market"
echo "State file: /tmp/neo_market_state.json"
echo "Call log: /tmp/neo_market_calls.jsonl"