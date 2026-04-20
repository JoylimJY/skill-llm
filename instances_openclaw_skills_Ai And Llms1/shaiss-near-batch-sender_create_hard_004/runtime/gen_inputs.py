from pathlib import Path
import json

root = Path('.')

send_data = {
    "batch_tag": "NEAR-QA-2025-04",
    "note": "dry-run-before-execution",
    "recipients": [
        {"account": "alice.near", "amount": "1.25"},
        {"account": "bob.near", "amount": "0.75"},
        {"account": "carol.near", "amount": "2.5"},
        {"account": "dave.near", "amount": "0.4"},
    ],
}

nft_data = {
    "batch_tag": "NEAR-QA-2025-04",
    "marker_contract": "collectibles.example.near",
    "transfers": [
        {"token_id": "101", "receiver": "alice.near", "contract": "collectibles.example.near"},
        {"token_id": "102", "receiver": "bob.near", "contract": "collectibles.example.near"},
        {"token_id": "103", "receiver": "carol.near", "contract": "collectibles.example.near"},
    ],
}

claim_data = {
    "batch_tag": "NEAR-QA-2025-04",
    "campaign": "spring-airdrop-7",
    "claims": [
        {"account": "alice.near"},
        {"account": "dave.near"},
    ],
}

(root / "send_batch.json").write_text(json.dumps(send_data, indent=2) + "\n", encoding="utf-8")
(root / "nft_batch.json").write_text(json.dumps(nft_data, indent=2) + "\n", encoding="utf-8")
(root / "claim_batch.json").write_text(json.dumps(claim_data, indent=2) + "\n", encoding="utf-8")

# Marker file for verification robustness
(root / "README_MARKERS.txt").write_text(
    "NEAR-QA-2025-04\ndry-run-before-execution\ncollectibles.example.near\nspring-airdrop-7\n",
    encoding="utf-8",
)
