import json
from pathlib import Path

# Deterministic marker content for verification
marker = "NEAR_BATCH_MARKER_2025_04"

send_data = {
    "marker": marker,
    "recipients": [
        {"account": "alice.near", "amount": "1.25"},
        {"account": "bob.near", "amount": "0.75"},
        {"account": "carol.near", "amount": "0.50"}
    ]
}

nft_data = {
    "marker": marker,
    "transfers": [
        {"token_id": "101", "receiver": "alice.near", "contract": "collectibles.near"},
        {"token_id": "102", "receiver": "bob.near", "contract": "collectibles.near"}
    ]
}

claim_data = {
    "marker": marker,
    "claims": [
        {"account": "alice.near", "source": "airdrop"},
        {"account": "bob.near", "source": "rewards"}
    ]
}

Path("send_batch.json").write_text(json.dumps(send_data, indent=2), encoding="utf-8")
Path("nft_batch.json").write_text(json.dumps(nft_data, indent=2), encoding="utf-8")
Path("claim_batch.json").write_text(json.dumps(claim_data, indent=2), encoding="utf-8")
