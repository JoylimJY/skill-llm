#!/usr/bin/env python3
import os
import json
import random

random.seed(42)

workspace = "/workspace"

# --- Create deeply nested distractor file structure ---
dirs = [
    "archive/bids/2024-q1",
    "archive/bids/2024-q2",
    "archive/deliveries/completed",
    "archive/deliveries/failed",
    "config/networks",
    "config/profiles",
    "ipfs_staging/proposals",
    "ipfs_staging/results",
    "logs/transactions",
    "logs/errors",
    "scripts/helpers",
    "tmp_work/data_analysis",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# --- Distractor files ---

# Old bid records (wrong format, outdated)
with open(os.path.join(workspace, "archive/bids/2024-q1/bid_job_14.json"), "w") as f:
    json.dump({
        "job_id": 14,
        "price": 500,
        "eta_hours": 2,  # NOTE: wrong unit - hours not seconds (a trap)
        "cid": "QmOldProposalNoPrefix",  # NOTE: missing ipfs:// prefix (a trap)
        "status": "rejected",
        "submitted": "2024-01-15T10:23:00Z"
    }, f, indent=2)

with open(os.path.join(workspace, "archive/bids/2024-q1/bid_job_17.json"), "w") as f:
    json.dump({
        "job_id": 17,
        "price": 420,
        "eta_hours": 4,
        "cid": "QmAnotherOldProposal",
        "status": "rejected",
        "submitted": "2024-01-22T08:45:00Z"
    }, f, indent=2)

with open(os.path.join(workspace, "archive/bids/2024-q2/bid_job_31.json"), "w") as f:
    json.dump({
        "job_id": 31,
        "price": 350,
        "eta_hours": 3,
        "cid": "QmQ2ProposalHash",
        "status": "accepted",
        "escrow_id": 22,
        "submitted": "2024-04-10T14:00:00Z"
    }, f, indent=2)

# Completed deliveries
with open(os.path.join(workspace, "archive/deliveries/completed/delivery_job_31.json"), "w") as f:
    json.dump({
        "job_id": 31,
        "escrow_id": 22,
        "result_cid": "ipfs://QmCompletedResult31",
        "delivered_at": "2024-04-10T17:00:00Z",
        "payment_tx": "0xabc123def456"
    }, f, indent=2)

with open(os.path.join(workspace, "archive/deliveries/failed/delivery_job_14.json"), "w") as f:
    json.dump({
        "job_id": 14,
        "escrow_id": None,
        "error": "Bid not selected",
        "delivered_at": None
    }, f, indent=2)

# Network configs (distractors)
with open(os.path.join(workspace, "config/networks/sepolia.json"), "w") as f:
    json.dump({
        "name": "Sepolia Testnet",
        "chain_id": 11155111,
        "rpc_url": "https://ethereum-sepolia-rpc.publicnode.com",
        "currency": "ETH",
        "usdc_address": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"
    }, f, indent=2)

with open(os.path.join(workspace, "config/networks/base.json"), "w") as f:
    json.dump({
        "name": "Base Mainnet",
        "chain_id": 8453,
        "rpc_url": "https://mainnet.base.org",
        "currency": "ETH",
        "usdc_address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
    }, f, indent=2)

# Profile configs
with open(os.path.join(workspace, "config/profiles/agent_profile_draft.json"), "w") as f:
    json.dump({
        "name": "DataCruncher-v2",
        "skills": ["data_analysis", "python", "ml_inference"],
        "reputation_score": 4.7,
        "completed_jobs": 31,
        "wallet": "0xDEADBEEF00000000000000000000000000000001",
        "note": "DRAFT - not yet registered on-chain"
    }, f, indent=2)

with open(os.path.join(workspace, "config/profiles/agent_profile_v1.json"), "w") as f:
    json.dump({
        "name": "DataCruncher-v1",
        "skills": ["data_analysis"],
        "ipfs_manifest": "QmOldManifestNoPrefixShouldNotUse",
        "registered": False
    }, f, indent=2)

# IPFS staging files
with open(os.path.join(workspace, "ipfs_staging/proposals/proposal_draft.md"), "w") as f:
    f.write("# Data Analysis Proposal\n\n## Approach\nWe will use pandas and scikit-learn...\n\n## Timeline\n2 hours\n\n## Price\n$380 USDC\n\nIPFS CID (once uploaded): ipfs://QmProposalXYZ789abc\n")

with open(os.path.join(workspace, "ipfs_staging/results/result_placeholder.txt"), "w") as f:
    f.write("Result CID will be: ipfs://QmResultABC123def\nUpload pending delivery confirmation.\n")

with open(os.path.join(workspace, "ipfs_staging/proposals/old_proposal_v1.txt"), "w") as f:
    f.write("Old proposal text. Do not use. CID: QmExpiredProposal999 (no prefix)\n")

# Log files (distractors with misleading content)
with open(os.path.join(workspace, "logs/transactions/tx_log_2024.jsonl"), "w") as f:
    entries = [
        {"ts": "2024-01-15T10:23:00Z", "type": "bid", "job": 14, "tx": "0x111aaa", "status": "mined"},
        {"ts": "2024-04-10T14:00:00Z", "type": "bid", "job": 31, "tx": "0x222bbb", "status": "mined"},
        {"ts": "2024-04-10T17:00:00Z", "type": "deliver", "job": 31, "escrow": 22, "tx": "0x333ccc", "status": "mined"},
    ]
    for e in entries:
        f.write(json.dumps(e) + "\n")

with open(os.path.join(workspace, "logs/errors/error_log.txt"), "w") as f:
    f.write("[2024-01-15 10:22:00] ERROR: Bid rejected - price too high (500 USDC > budget 450 USDC)\n")
    f.write("[2024-04-10 13:59:00] INFO: Bid accepted for job 31, escrow created ID=22\n")
    f.write("[2024-04-10 16:59:00] INFO: Delivery confirmed, payment released\n")

# Helper scripts (distractors - misleading helper that uses wrong params)
with open(os.path.join(workspace, "scripts/helpers/auto_bid.sh"), "w") as f:
    f.write("#!/bin/bash\n# DEPRECATED - do not use\n# neo-market bid --job $1 --price $2 --eta $3 --cid $4\necho 'This script is deprecated'\n")
os.chmod(os.path.join(workspace, "scripts/helpers/auto_bid.sh"), 0o755)

with open(os.path.join(workspace, "scripts/helpers/submit_delivery.sh"), "w") as f:
    f.write("#!/bin/bash\n# DEPRECATED\n# Old syntax: neo-market deliver --job $1 --cid $2\n# Missing escrow param!\necho 'Missing escrow - this will fail'\n")
os.chmod(os.path.join(workspace, "scripts/helpers/submit_delivery.sh"), 0o755)

# Tmp work area
with open(os.path.join(workspace, "tmp_work/data_analysis/analysis_notes.txt"), "w") as f:
    f.write("Data analysis complete. Summary: 3 clusters identified, p-value < 0.05.\n")
    f.write("Output ready for delivery.\n")
    f.write("Proposal CID: ipfs://QmProposalXYZ789abc\n")
    f.write("Result CID:   ipfs://QmResultABC123def\n")

# A misleading "instructions.txt" that gives wrong parameter values
with open(os.path.join(workspace, "tmp_work/data_analysis/instructions_old.txt"), "w") as f:
    f.write("Job parameters (OUTDATED - verify against live market):\n")
    f.write("  Job ID: 5\n")  # wrong job id (trap)
    f.write("  Budget: $500 USDC\n")
    f.write("  ETA: 2 hours\n")  # ambiguous unit (trap - must convert to seconds)
    f.write("  Escrow: 3\n")    # wrong escrow (trap)

print("Workspace initialized successfully.")
print(f"Created {len(dirs)} directories and multiple distractor files.")