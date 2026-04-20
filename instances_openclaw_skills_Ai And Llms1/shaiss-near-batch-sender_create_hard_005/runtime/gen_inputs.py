import json
from pathlib import Path

# Deterministic fixture with embedded marker content for evaluation
payload = {
    "recipients": [
        {"account": "alice.near", "amount": "1.25"},
        {"account": "bob.near", "amount": "0.75"},
        {"account": "carol.near", "amount": "2.00"}
    ],
    "transfers": [
        {"token_id": "1001", "receiver": "dave.near", "contract": "art.nft.near"},
        {"token_id": "1002", "receiver": "erin.near", "contract": "art.nft.near"}
    ],
    "claims": [
        {"source": "airdrop-1", "account": "alice.near"},
        {"source": "airdrop-2", "account": "bob.near"}
    ],
    "marker": "NEAR_BATCH_TASK_MARKER_V1"
}

Path("batch_input.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
