#!/usr/bin/env python3
"""
Build the sandbox workspace with realistic distractor files and the
core problem input: a raw chat log containing a hidden Cashu token
embedded in an emoji.
"""
import os
import subprocess
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── 1. Distractor directory tree ────────────────────────────────────────────
dirs = [
    "marketplace/orders/2024-Q1",
    "marketplace/orders/2024-Q2",
    "marketplace/products/digital",
    "marketplace/products/physical",
    "marketplace/payments/receipts",
    "marketplace/payments/pending",
    "marketplace/logs/system",
    "marketplace/logs/audit",
    "marketplace/config",
    "marketplace/exports",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractor_files = {
    "marketplace/orders/2024-Q1/order_001.json": json.dumps({"order_id": "ORD-001", "status": "fulfilled", "amount_sat": 500}),
    "marketplace/orders/2024-Q1/order_002.json": json.dumps({"order_id": "ORD-002", "status": "pending", "amount_sat": 210}),
    "marketplace/orders/2024-Q2/order_045.json": json.dumps({"order_id": "ORD-045", "status": "cancelled", "amount_sat": 100}),
    "marketplace/products/digital/ebook_catalog.csv": "id,title,price_sat\n1,\"Bitcoin Basics\",100\n2,\"LN Deep Dive\",250\n3,\"Cashu Handbook\",50\n",
    "marketplace/products/physical/inventory.txt": "item_id,qty,sku\nA1,10,GADGET-001\nB2,3,WIDGET-007\n",
    "marketplace/payments/receipts/receipt_29a.txt": "Payment received: 100 sat — ref #29a",
    "marketplace/payments/receipts/receipt_30b.txt": "Payment received: 50 sat — ref #30b",
    "marketplace/payments/pending/unconfirmed.log": "2024-01-15T12:00:00Z — awaiting confirmation for order ORD-046\n",
    "marketplace/logs/system/app.log": "INFO 2024-01-15 startup ok\nWARN 2024-01-15 slow query\nINFO 2024-01-15 shutdown\n",
    "marketplace/logs/audit/access.log": "GET /api/orders 200\nPOST /api/checkout 201\nGET /api/products 200\n",
    "marketplace/config/settings.json": json.dumps({"currency": "sat", "mint_default": "https://mint.minibits.cash/Bitcoin", "notify": True}),
    "marketplace/exports/monthly_summary.csv": "month,revenue_sat,orders\n2024-01,4500,12\n2024-02,6100,18\n",
    "tmp/scratch.txt": "temporary notes\n- check pending payments\n- update catalog\n",
}

for rel_path, content in distractor_files.items():
    full_path = os.path.join(WORKSPACE, rel_path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── 2. Generate the real Cashu token via encoding, then build the chat message ─
# We first encode a known token string into the peanut emoji to produce the
# hidden-emoji payload, then wrap it in realistic chat noise.

# A real-looking (but synthetic) CashuB token — short enough to embed reliably.
# This is the token we want the agent to decode and re-encode.
CASHU_TOKEN = (
    "cashuBo2FtgaJhaSJhcKNhYQFhc3hAMDA4MDRlMTc5YjA2MDRhNTQ3M"
    "zk5MmUyNmE5ZGNlNzFiNzU4Y2U2MzJhYWIxMDE5MTg3OWJlN2M1OTc"
    "5YWFjWCEDDn0NdS5gxCd5gKVPkOmJmhKi4fScEt_UcJh-PV7_cmFtaH"
    "R0cHM6Ly9taW50Lm1pbmliYXRzLmNhc2gvQml0Y29pbg"
)

# Encode the token into 🥜 using the CLI
encode_result = subprocess.run(
    ["node", "/opt/cashu-emoji/bin/cashu-emoji.js", "encode", "🥜", CASHU_TOKEN],
    capture_output=True, text=True
)
encoded_emoji = encode_result.stdout.strip()
print(f"[gen_inputs] Encoded emoji length: {len(encoded_emoji)} chars")
print(f"[gen_inputs] Encode stderr: {encode_result.stderr.strip()}")

# ── 3. Build a realistic, noisy chat message ─────────────────────────────────
# The emoji is embedded inside a multi-line chat log with surrounding text.
# NOTE: The file must preserve the raw Unicode bytes exactly.
chat_message = (
    "=== Customer Support Chat Log — Ticket #TX-2024-0892 ===\n"
    "Timestamp: 2024-01-15 14:32:07 UTC\n"
    "Customer [14:32]: Hey, I sent you the payment for order ORD-046, here it is:\n"
    f"{encoded_emoji}\n"
    "Customer [14:32]: Let me know once you confirm receipt!\n"
    "Support  [14:35]: Thanks, looking into it now.\n"
    "=== END OF LOG ===\n"
)

chat_log_path = os.path.join(WORKSPACE, "marketplace/payments/pending/chat_log_TX-2024-0892.txt")
with open(chat_log_path, "w", encoding="utf-8") as f:
    f.write(chat_message)

print(f"[gen_inputs] Chat log written to {chat_log_path}")
print(f"[gen_inputs] Expected token (first 40 chars): {CASHU_TOKEN[:40]}")

# Store the expected token in a hidden reference file for the eval script
ref = {
    "expected_token_prefix": CASHU_TOKEN[:60],
    "full_token": CASHU_TOKEN,
    "chat_log_path": chat_log_path,
}
with open(os.path.join(WORKSPACE, ".eval_ref.json"), "w") as f:
    json.dump(ref, f)

print("[gen_inputs] Done.")