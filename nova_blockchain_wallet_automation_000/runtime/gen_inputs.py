#!/usr/bin/env python3
"""
Generate a realistic sandbox workspace for the nova wallet audit task.
"""
import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Deep distractor directory structure ──────────────────────────────────────
dirs = [
    "treasury/reports/q3_2025",
    "treasury/reports/q4_2025",
    "treasury/config/networks",
    "treasury/config/wallets",
    "treasury/scripts/deprecated",
    "treasury/scripts/active",
    "ops/audit/blockchain",
    "ops/audit/fiat",
    "ops/monitoring/alerts",
    "compliance/kyc",
    "compliance/aml",
    "finance/ledger",
    "finance/reconciliation",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── Distractor files (realistic but irrelevant) ───────────────────────────────
distractors = {
    "treasury/reports/q3_2025/balance_snapshot.csv": (
        "date,network,asset,amount_usd\n"
        "2025-07-01,mainnet,USDC,142300.50\n"
        "2025-07-01,mainnet,USDT,89200.00\n"
        "2025-07-01,testnet,USDC,5000.00\n"
    ),
    "treasury/reports/q4_2025/projected_flows.txt": (
        "Q4 2025 Projected Treasury Flows\n"
        "Estimated withdrawals: $250,000\n"
        "Estimated receipts: $310,000\n"
        "Net: +$60,000\n"
    ),
    "treasury/config/networks/mainnet.json": json.dumps({
        "name": "mainnet",
        "rpc_endpoint": "https://rpc.mynth.ai",
        "chain_id": 1,
        "explorer": "https://explorer.mynth.ai"
    }, indent=2),
    "treasury/config/networks/testnet.json": json.dumps({
        "name": "testnet",
        "rpc_endpoint": "https://testnet-rpc.mynth.ai",
        "chain_id": 99,
        "explorer": "https://testnet-explorer.mynth.ai"
    }, indent=2),
    "treasury/config/wallets/known_addresses.json": json.dumps({
        "sui_treasury_hot": "0xdeadbeef1234567890abcdef1234567890abcdef1234567890abcdef12345678",
        "base_cold_storage": "0xaBcDeF1234567890aBcDeF1234567890aBcDeF12",
        "solana_ops": "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
    }, indent=2),
    "treasury/scripts/deprecated/old_withdraw.sh": (
        "#!/bin/bash\n"
        "# DEPRECATED - do not use\n"
        "# nova withdraw $1 USDC $2 sui\n"
        "echo 'This script is deprecated'\n"
    ),
    "treasury/scripts/active/network_check.sh": (
        "#!/bin/bash\n"
        "# Placeholder - agent should use nova CLI directly\n"
        "echo 'Use nova config get network'\n"
    ),
    "ops/audit/blockchain/audit_template.json": json.dumps({
        "audit_id": "TEMPLATE",
        "auditor": "",
        "timestamp": "",
        "network": "",
        "balance_usd": None,
        "withdrawal_dry_run": {
            "status": "",
            "amount": "",
            "stablecoin": "",
            "blockchain": "",
            "address": "",
            "valid": None
        }
    }, indent=2),
    "ops/audit/blockchain/previous_audit_2025_06.json": json.dumps({
        "audit_id": "AUDIT-2025-06-15",
        "auditor": "ops-team",
        "timestamp": "2025-06-15T09:00:00Z",
        "network": "testnet",
        "balance_usd": "1250.00",
        "withdrawal_dry_run": {
            "status": "ok",
            "amount": "100",
            "stablecoin": "USDT",
            "blockchain": "tron",
            "address": "TRqxyzTestAddress12345",
            "valid": True
        }
    }, indent=2),
    "ops/monitoring/alerts/rate_limit_log.txt": (
        "2025-07-10 14:32:11 WARN  Rate limited on nova send. Waited 30s.\n"
        "2025-07-10 14:32:41 INFO  Retried nova balance. Success.\n"
    ),
    "compliance/kyc/approved_counterparties.csv": (
        "entity_id,name,kyc_level,approved_blockchains\n"
        "ENT-001,Acme Corp,L2,sui;solana;base\n"
        "ENT-002,Beta Finance,L3,cardano;tron\n"
    ),
    "compliance/aml/flagged_addresses.txt": (
        "# Flagged addresses - DO NOT SEND\n"
        "0x000000000000000000000000000000000000dead\n"
        "TRflaggedAddress99999\n"
    ),
    "finance/ledger/transactions_july.csv": (
        "tx_id,type,amount,stablecoin,blockchain,status\n"
        "TX001,withdraw,500,USDC,base,completed\n"
        "TX002,send,25,,nova,completed\n"
        "TX003,withdraw,1000,USDT,tron,pending\n"
    ),
    "finance/reconciliation/notes.txt": (
        "Reconciliation Notes - July 2025\n"
        "- TX003 pending chain confirmation\n"
        "- Sui withdrawal planned for Q4 test: 50 USDT (testnet)\n"
        "- Remember: testnet sui uses USDT, not USDC!\n"
    ),
}

for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# ── Task specification file (business context, no hints about CLI flags) ─────
task_spec = {
    "task_id": "AUDIT-2025-07-TESTNET-SUI",
    "requested_by": "Head of Treasury Operations",
    "description": (
        "Perform a pre-promotion audit of the testnet wallet before we move "
        "to mainnet operations. We need three things:\n"
        "1. Confirm we are on the correct test environment.\n"
        "2. Check the current wallet balance.\n"
        "3. Validate (without actually sending) a planned withdrawal of 50 USD "
        "   to the SUI blockchain address below, using the appropriate stablecoin "
        "   for our test environment.\n"
        "The SUI destination address: "
        "0xa1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f9"
    ),
    "sui_destination": "0xa1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f9",
    "planned_amount": 50,
    "target_blockchain": "sui",
    "environment": "testnet",
    "output_file": "audit_report.json",
}
(workspace / "task_spec.json").write_text(json.dumps(task_spec, indent=2))

print("Workspace generated successfully.")
print(f"Files created: {len(list(workspace.rglob('*')))} items")