import json
import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Distractor directory structure ---
dirs = [
    "internal/finance/q3_reports",
    "internal/finance/q4_reports",
    "internal/engineering/backend/payments",
    "internal/engineering/backend/legacy",
    "internal/engineering/infra/monitoring",
    "internal/legal/compliance/crypto",
    "internal/legal/compliance/kyc",
    "internal/marketing/campaigns/2024",
    "internal/ops/runbooks",
    "internal/ops/oncall",
    "data/raw/blockchain/bitcoin",
    "data/raw/blockchain/ethereum",
    "data/processed/reports",
    "data/processed/exports",
    "configs/prod",
    "configs/staging",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

distractor_files = {
    "internal/finance/q3_reports/btc_holdings.csv": "address,amount\n1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf6N,0.5\n3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy,1.2",
    "internal/finance/q4_reports/eth_summary.txt": "ETH addresses do not start with D. Total Q4 revenue: $45,200.",
    "internal/engineering/backend/payments/stripe_config.json": json.dumps({"provider": "stripe", "currency": "USD", "version": "2023-10"}),
    "internal/engineering/backend/legacy/old_payment_flow.py": "# Deprecated: uses XRP with memo tags\ndef send_xrp(address, memo): pass",
    "internal/engineering/backend/payments/fee_calculator.py": "# Bitcoin fee calculator - DO NOT USE FOR DOGE\ndef btc_fee(sat_per_vbyte): return sat_per_vbyte * 250",
    "internal/engineering/infra/monitoring/alerts.yaml": "alerts:\n  - name: high_fee\n    threshold: 0.01 BTC\n  - name: low_balance\n    threshold: 0.001 ETH",
    "internal/legal/compliance/crypto/xrp_memo_policy.md": "All XRP transactions MUST include a memo/destination tag per regulatory policy.",
    "internal/legal/compliance/kyc/checklist.txt": "1. ID verification\n2. Address proof\n3. Source of funds",
    "internal/marketing/campaigns/2024/doge_promo.txt": "We love DOGE! Fast, fun, and furry. Ask users to double their DOGE for free!",
    "internal/ops/runbooks/btc_rbf_guide.md": "# Bitcoin RBF Guide\nIf a BTC transaction is stuck, use Replace-By-Fee to rebroadcast with higher fee.",
    "internal/ops/oncall/escalation_policy.txt": "P1: Page on-call engineer\nP2: Slack alert\nP3: Email next business day",
    "data/raw/blockchain/bitcoin/mempool_snapshot.json": json.dumps({"chain": "bitcoin", "pending_txs": 1200, "avg_fee_sat_vbyte": 45}),
    "data/raw/blockchain/ethereum/gas_prices.json": json.dumps({"chain": "ethereum", "base_fee_gwei": 12, "priority_fee_gwei": 2}),
    "configs/prod/payment_gateway.json": json.dumps({"gateway": "legacy_v1", "timeout_ms": 5000, "retry": 3}),
    "configs/staging/feature_flags.json": json.dumps({"enable_rbf": True, "enable_segwit": True, "enable_taproot": False}),
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w") as f:
        f.write(content)

# --- MAIN INPUT DATA ---
# 1. Messy wallet address list for validation
# Addresses: mix of valid DOGE, Bitcoin-style, Litecoin-style, wrong length, wrong case-sensitivity-irrelevant but wrong prefix, etc.
addresses_raw = {
    "addresses": [
        # Valid DOGE addresses (start with D, exactly 34 chars)
        {"id": "addr_001", "address": "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L", "label": "merchant_primary"},
        {"id": "addr_002", "address": "D7Y55jfHm6fjKqY6YBR7zAhzXkfGHqdamH", "label": "hot_wallet"},
        {"id": "addr_003", "address": "DNHvMjHUmYHMdFWfqpSmNqRtfHvNz4R7Dp", "label": "cold_storage"},
        # Invalid: Bitcoin-style (starts with 1)
        {"id": "addr_004", "address": "1A1zP1eP5QGefi2DMPTfTL5SLmv7Divf6N", "label": "customer_refund_old"},
        # Invalid: starts with D but wrong length (33 chars)
        {"id": "addr_005", "address": "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7", "label": "truncated_entry"},
        # Invalid: starts with D but wrong length (35 chars)
        {"id": "addr_006", "address": "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7LXX", "label": "extra_chars"},
        # Invalid: Litecoin-style (starts with L)
        {"id": "addr_007", "address": "LdP8Qox1VAhCzLnqQXejhzZcg3Lh65Tdf4", "label": "mistaken_ltc"},
        # Valid DOGE address
        {"id": "addr_008", "address": "DBs4WcRE7eysKmLra237DUvkzCQTBRsvhG", "label": "partner_payout"},
        # Invalid: starts with 3 (Bitcoin P2SH)
        {"id": "addr_009", "address": "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", "label": "old_p2sh_attempt"},
        # Invalid: starts with D but contains spaces (malformed)
        {"id": "addr_010", "address": "D H5yaieqoZN36fDVciNyRueRGvGLR3mr7L", "label": "copy_paste_error"},
        # Valid DOGE address
        {"id": "addr_011", "address": "DPpJbySLKeMqhvB7LZbJhXNiReFEniZB3j", "label": "reserve_wallet"},
        # Invalid: starts with d (lowercase, DOGE addresses are case-sensitive and start uppercase D)
        {"id": "addr_012", "address": "dH5yaieqoZN36fDVciNyRueRGvGLR3mr7L", "label": "lowercase_prefix"},
    ]
}

with open(os.path.join(workspace, "data/raw/blockchain/bitcoin/unused_btc.json"), "w") as f:
    json.dump({"note": "not dogecoin data"}, f)

with open(os.path.join(workspace, "data/processed/wallet_addresses_raw.json"), "w") as f:
    json.dump(addresses_raw, f, indent=2)

# 2. UTXO dataset for fee/dust analysis
# Fee rate: 1 DOGE per KB (1000 bytes). Transactions are sized in bytes.
# Dust: if fee_to_spend > utxo_value, it's dust.
# fee_to_spend = (tx_size_bytes / 1000) * 1.0  (1 DOGE per KB)
# We'll give tx_size_bytes for spending each UTXO (a standard input is ~148 bytes but let's use realistic messy values)

utxos_raw = {
    "wallet_id": "hot_wallet_primary",
    "currency": "DOGE",
    "utxos": [
        # Normal UTXOs
        {"utxo_id": "utxo_001", "value_doge": 500.0, "tx_size_bytes": 226, "confirmations": 8, "label": "customer_payment_1"},
        {"utxo_id": "utxo_002", "value_doge": 1200.5, "tx_size_bytes": 226, "confirmations": 15, "label": "exchange_withdrawal"},
        {"utxo_id": "utxo_003", "value_doge": 0.0003, "tx_size_bytes": 148, "confirmations": 3, "label": "tip_received_tiny"},  # dust: fee=0.000148 DOGE, value=0.0003 — NOT dust (0.000148 < 0.0003)
        {"utxo_id": "utxo_004", "value_doge": 0.00005, "tx_size_bytes": 148, "confirmations": 10, "label": "micro_tip"},  # dust: fee=0.000148 > 0.00005 -> DUST
        {"utxo_id": "utxo_005", "value_doge": 50000.0, "tx_size_bytes": 374, "confirmations": 2, "label": "large_merchant_payment"},  # high value, low confirmations
        {"utxo_id": "utxo_006", "value_doge": 0.001, "tx_size_bytes": 148, "confirmations": 7, "label": "faucet_drip"},  # fee=0.000148 < 0.001 -> NOT dust
        {"utxo_id": "utxo_007", "value_doge": 0.0001, "tx_size_bytes": 192, "confirmations": 1, "label": "nano_payment"},  # dust: fee=0.000192 > 0.0001 -> DUST
        {"utxo_id": "utxo_008", "value_doge": 750.25, "tx_size_bytes": 226, "confirmations": 0, "label": "just_received"},  # unconfirmed
        {"utxo_id": "utxo_009", "value_doge": 10.0, "tx_size_bytes": 520, "confirmations": 12, "label": "consolidated_batch"},  # large tx due to many inputs
        {"utxo_id": "utxo_010", "value_doge": 0.00008, "tx_size_bytes": 148, "confirmations": 5, "label": "dust_borderline"},  # fee=0.000148 > 0.00008 -> DUST
    ]
}

with open(os.path.join(workspace, "data/raw/blockchain/doge_utxos_raw.json"), "w") as f:
    json.dump(utxos_raw, f, indent=2)

# 3. Pending transactions for risk classification
# Risk rules from SKILL.md:
# - 0 confirmations: UNCONFIRMED (cannot RBF)
# - 1-5 confirmations: LOW_CONFIDENCE (basic confirmed but not high-value threshold)
# - 6+ confirmations: CONFIRMED (safe for high-value)
# - Exchange threshold: 6-20 confirmations
# - No RBF available
# - Amounts >= 10000 DOGE flagged as HIGH_VALUE (requiring 6 conf)

transactions_raw = {
    "pending_review": [
        {"tx_id": "tx_aabb1122", "amount_doge": 250.0, "confirmations": 0, "destination": "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L", "note": "customer purchase"},
        {"tx_id": "tx_ccdd3344", "amount_doge": 15000.0, "confirmations": 3, "destination": "D7Y55jfHm6fjKqY6YBR7zAhzXkfGHqdamH", "note": "bulk payout"},
        {"tx_id": "tx_eeff5566", "amount_doge": 99.9, "confirmations": 6, "destination": "DNHvMjHUmYHMdFWfqpSmNqRtfHvNz4R7Dp", "note": "subscription fee"},
        {"tx_id": "tx_aabb9900", "amount_doge": 500000.0, "confirmations": 1, "destination": "DBs4WcRE7eysKmLra237DUvkzCQTBRsvhG", "note": "whale transfer"},
        {"tx_id": "tx_1234abcd", "amount_doge": 10.0, "confirmations": 10, "destination": "DPpJbySLKeMqhvB7LZbJhXNiReFEniZB3j", "note": "tip jar"},
        {"tx_id": "tx_5678efgh", "amount_doge": 25000.0, "confirmations": 0, "destination": "DH5yaieqoZN36fDVciNyRueRGvGLR3mr7L", "note": "urgent payout"},
        {"tx_id": "tx_9999zzzz", "amount_doge": 1.0, "confirmations": 4, "destination": "DBs4WcRE7eysKmLra237DUvkzCQTBRsvhG", "note": "fee test"},
    ]
}

with open(os.path.join(workspace, "data/raw/blockchain/doge_pending_txs.json"), "w") as f:
    json.dump(transactions_raw, f, indent=2)

# 4. A misleading memo/tag config file (distractor suggesting DOGE needs memos like XRP)
memo_config = {
    "payment_config": {
        "xrp": {"requires_memo": True, "memo_type": "destination_tag"},
        "doge": {"requires_memo": "UNKNOWN", "memo_type": "UNKNOWN"},
        "btc": {"requires_memo": False, "memo_type": None}
    },
    "notes": "Please fill in DOGE memo requirement before Q4 launch"
}
with open(os.path.join(workspace, "configs/prod/payment_memo_config.json"), "w") as f:
    json.dump(memo_config, f, indent=2)

# 5. An RBF config suggesting DOGE supports it (distractor from ops team)
rbf_policy = {
    "rbf_enabled_chains": ["bitcoin", "dogecoin", "litecoin"],
    "rbf_min_fee_bump_percent": 10,
    "note": "Auto-enable RBF for all stuck transactions"
}
with open(os.path.join(workspace, "configs/staging/rbf_policy.json"), "w") as f:
    json.dump(rbf_policy, f, indent=2)

print("Workspace generated successfully.")
print(f"Files created in {workspace}")