import os
import random
import csv
import json

random.seed(42)

# Create directory structure
dirs = [
    "workspace/ops/transactions/incoming",
    "workspace/ops/transactions/outgoing",
    "workspace/ops/wallets/primary",
    "workspace/ops/wallets/archived",
    "workspace/compliance/reports/2023",
    "workspace/compliance/reports/2024",
    "workspace/compliance/flagged",
    "workspace/finance/reconciliation",
    "workspace/finance/invoices",
    "workspace/internal/configs",
    "workspace/internal/logs",
    "workspace/internal/backups",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# --- Distractor files ---
with open("workspace/internal/configs/node_config.txt", "w") as f:
    f.write("host=node.community.example\nport=18089\ntimeout=30\nmax_connections=8\n")

with open("workspace/internal/logs/sync_log.txt", "w") as f:
    f.write("2024-01-15 08:00:01 INFO  Sync started\n")
    f.write("2024-01-15 08:45:22 INFO  Block height 3100000 reached\n")
    f.write("2024-01-15 09:10:05 WARN  Daemon disconnected, retrying\n")
    f.write("2024-01-15 09:11:00 INFO  Reconnected to daemon\n")

with open("workspace/internal/backups/wallet_backup_notes.txt", "w") as f:
    f.write("Last backup: 2024-03-01\nSeed stored in secure vault.\nDo not share with anyone.\n")

with open("workspace/finance/invoices/invoice_2024_001.txt", "w") as f:
    f.write("Invoice #2024-001\nAmount: 1.5 XMR\nDate: 2024-03-15\nStatus: Pending\n")

with open("workspace/finance/invoices/invoice_2024_002.txt", "w") as f:
    f.write("Invoice #2024-002\nAmount: 0.75 XMR\nDate: 2024-04-02\nStatus: Paid\n")

with open("workspace/finance/reconciliation/q1_summary.txt", "w") as f:
    f.write("Q1 2024 Summary\nTotal Received: 22.3 XMR\nTotal Sent: 18.1 XMR\nNet: 4.2 XMR\n")

with open("workspace/ops/wallets/archived/old_wallet_notes.md", "w") as f:
    f.write("# Archived Wallet\n\nThis wallet was decommissioned in 2023.\nFunds transferred to new subaddress-based wallet.\n")

with open("workspace/compliance/reports/2023/annual_report.txt", "w") as f:
    f.write("Annual Compliance Report 2023\nAll transactions reviewed.\nNo suspicious activity found.\n")

with open("workspace/compliance/flagged/manual_review_notes.txt", "w") as f:
    f.write("Case #001: Large withdrawal, pending manual review\nCase #002: Address reuse detected on legacy wallet\n")

with open("workspace/ops/transactions/outgoing/batch_march.txt", "w") as f:
    f.write("Batch outgoing March 2024 - 14 transactions processed, fees totaled 0.42 XMR\n")

with open("workspace/internal/configs/fee_settings.txt", "w") as f:
    f.write("priority=normal\nestimated_fee_usd_min=0.01\nestimated_fee_usd_max=0.05\n")

# -----------------------------------------------------------------------
# THE ACTUAL PROBLEM FILE: messy_transactions.csv
# -----------------------------------------------------------------------
# Fields: tx_id, address, address_type_claimed, amount_xmr, block_height_received,
#         current_block_height, confirmations_at_time_of_report, tx_key_provided,
#         payment_id_provided, notes
#
# The agent must:
# 1. Validate addresses against Monero rules (prefix + length)
# 2. Determine if address_type_claimed matches real type
# 3. Compute whether funds are unlocked (received_block + 10 <= current_block)
# 4. Determine if sufficiently confirmed (>= 10 confirmations)
# 5. Check payment verification fields (needs tx_key + tx_id + recipient address)
# 6. Flag issues and produce compliance_report.json

transactions = [
    # tx_id, address, address_type_claimed, amount_xmr, block_height_received,
    # current_block_height, confirmations, tx_key_provided, notes

    # VALID: standard address, correct prefix "4", 95 chars, 12 confs, unlocked
    {
        "tx_id": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a100",
        "address": "4" + "A" * 94,  # 95 chars, starts with 4
        "address_type_claimed": "standard",
        "amount_xmr": "2.500000",
        "block_height_received": "3100000",
        "current_block_height": "3100015",
        "confirmations": "15",
        "tx_key_provided": "yes",
        "payment_id_provided": "no",
        "notes": "Normal corporate payment"
    },
    # INVALID: claims "subaddress" but starts with "4" (should be "8")
    {
        "tx_id": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b200",
        "address": "4" + "B" * 94,  # starts with 4 but claimed subaddress
        "address_type_claimed": "subaddress",
        "amount_xmr": "0.750000",
        "block_height_received": "3100005",
        "current_block_height": "3100015",
        "confirmations": "10",
        "tx_key_provided": "no",
        "payment_id_provided": "no",
        "notes": "Vendor payout - address claimed as subaddress"
    },
    # VALID subaddress: starts with "8", 95 chars, 11 confs, unlocked
    {
        "tx_id": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1c300",
        "address": "8" + "C" * 94,  # 95 chars, starts with 8
        "address_type_claimed": "subaddress",
        "amount_xmr": "1.250000",
        "block_height_received": "3100002",
        "current_block_height": "3100013",
        "confirmations": "11",
        "tx_key_provided": "yes",
        "payment_id_provided": "no",
        "notes": "Preferred receiving address"
    },
    # LOCKED: only 8 confirmations, also unlock not reached (received=3100010, current=3100017 => diff=7 < 10)
    {
        "tx_id": "d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1d400",
        "address": "8" + "D" * 94,
        "address_type_claimed": "subaddress",
        "amount_xmr": "5.000000",
        "block_height_received": "3100010",
        "current_block_height": "3100017",
        "confirmations": "7",
        "tx_key_provided": "yes",
        "payment_id_provided": "no",
        "notes": "Large incoming, recent"
    },
    # INVALID address: wrong length (only 90 chars), claimed standard
    {
        "tx_id": "e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2e500",
        "address": "4" + "E" * 89,  # only 90 chars, too short
        "address_type_claimed": "standard",
        "amount_xmr": "0.100000",
        "block_height_received": "3099990",
        "current_block_height": "3100015",
        "confirmations": "25",
        "tx_key_provided": "no",
        "payment_id_provided": "no",
        "notes": "Suspicious short address"
    },
    # INTEGRATED address: starts with 4, has payment_id_provided=yes, claimed integrated
    {
        "tx_id": "f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3f600",
        "address": "4" + "F" * 94,  # integrated also starts with 4
        "address_type_claimed": "integrated",
        "amount_xmr": "3.000000",
        "block_height_received": "3099950",
        "current_block_height": "3100015",
        "confirmations": "65",
        "tx_key_provided": "yes",
        "payment_id_provided": "yes",
        "notes": "Exchange deposit with payment ID"
    },
    # UNDER-CONFIRMED: 5 confs only, but unlocked (received=3099990, current=3100015, diff=25 >= 10)
    {
        "tx_id": "a7b8c9d0e1f2a7b8c9d0e1f2a7b8c9d0e1f2a7b8c9d0e1f2a7b8c9d0a700",
        "address": "8" + "G" * 94,
        "address_type_claimed": "subaddress",
        "amount_xmr": "0.500000",
        "block_height_received": "3099990",
        "current_block_height": "3100015",
        "confirmations": "5",
        "tx_key_provided": "no",
        "payment_id_provided": "no",
        "notes": "Partial confirmation - do not release funds"
    },
    # VALID but no tx_key - payment cannot be cryptographically proven
    {
        "tx_id": "b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1b800",
        "address": "4" + "H" * 94,
        "address_type_claimed": "standard",
        "amount_xmr": "1.800000",
        "block_height_received": "3099900",
        "current_block_height": "3100015",
        "confirmations": "115",
        "tx_key_provided": "no",
        "payment_id_provided": "no",
        "notes": "Old payment, no tx_key retained"
    },
    # STUCK/problematic: confirmations=0, cannot use RBF, note says "trying to bump fee"
    {
        "tx_id": "c9d0e1f2a3b4c9d0e1f2a3b4c9d0e1f2a3b4c9d0e1f2a3b4c9d0e1f2c900",
        "address": "8" + "I" * 94,
        "address_type_claimed": "subaddress",
        "amount_xmr": "0.250000",
        "block_height_received": "3100015",
        "current_block_height": "3100015",
        "confirmations": "0",
        "tx_key_provided": "yes",
        "payment_id_provided": "no",
        "notes": "Fee bump requested - operator trying RBF"
    },
    # INVALID: address starts with "9" - not valid for any Monero address type
    {
        "tx_id": "d0e1f2a3b4c5d0e1f2a3b4c5d0e1f2a3b4c5d0e1f2a3b4c5d0e1f2a3d000",
        "address": "9" + "J" * 94,  # invalid prefix
        "address_type_claimed": "standard",
        "amount_xmr": "0.050000",
        "block_height_received": "3100000",
        "current_block_height": "3100015",
        "confirmations": "15",
        "tx_key_provided": "no",
        "payment_id_provided": "no",
        "notes": "Unknown address format"
    },
]

fieldnames = [
    "tx_id", "address", "address_type_claimed", "amount_xmr",
    "block_height_received", "current_block_height", "confirmations",
    "tx_key_provided", "payment_id_provided", "notes"
]

csv_path = "workspace/ops/transactions/incoming/messy_transactions.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for tx in transactions:
        writer.writerow(tx)

# Also write a wallet address registry with some messy data for context
wallet_data = [
    {"wallet_id": "W001", "address": "4" + "A" * 94, "type": "standard", "active": "yes"},
    {"wallet_id": "W002", "address": "8" + "C" * 94, "type": "subaddress", "active": "yes"},
    {"wallet_id": "W003", "address": "4" + "F" * 94, "type": "integrated", "active": "yes"},
    {"wallet_id": "W004", "address": "4" + "X" * 94, "type": "standard", "active": "no"},
    {"wallet_id": "W005", "address": "8" + "D" * 94, "type": "subaddress", "active": "yes"},
]
with open("workspace/ops/wallets/primary/wallet_registry.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["wallet_id", "address", "type", "active"])
    writer.writeheader()
    for w in wallet_data:
        writer.writerow(w)

# Write a messy operational memo with intentionally wrong advice to trap naive agents
with open("workspace/compliance/flagged/ops_memo.txt", "w") as f:
    f.write(
        "INTERNAL MEMO - DO NOT DISTRIBUTE\n"
        "=================================\n"
        "Per Bitcoin standards, we consider 6 confirmations to be final.\n"
        "Fee bumping via RBF is available if transactions get stuck.\n"
        "Standard addresses are 34 characters starting with 1 or 3.\n"
        "All outgoing transactions should include a memo/tag field.\n"
        "Note: View key shows ALL transactions including outgoing.\n"
        "(This memo is outdated and contains errors - do not rely on it)\n"
    )

print("Workspace generated successfully.")
print(f"CSV written to: {csv_path}")
print(f"Wallet registry written to: workspace/ops/wallets/primary/wallet_registry.csv")