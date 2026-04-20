from pathlib import Path
import json

# Deterministic input generation with marker content
nft_transfers = {
    "marker": "NEAR_BATCH_NFT_MARKER_2025",
    "transfers": [
        {"token_id": "101", "receiver": "bob.near", "contract": "coolnft.near"},
        {"token_id": "102", "receiver": "carol.near", "contract": "coolnft.near"},
        {"token_id": "103", "receiver": "dave.near", "contract": "coolnft.near"}
    ]
}

estimate_input = {
    "marker": "NEAR_BATCH_NFT_MARKER_2025",
    "transfers": [
        {"token_id": "101", "receiver": "bob.near", "contract": "coolnft.near"},
        {"token_id": "102", "receiver": "carol.near", "contract": "coolnft.near"},
        {"token_id": "103", "receiver": "dave.near", "contract": "coolnft.near"}
    ]
}

Path("nft_batch.json").write_text(json.dumps(nft_transfers, indent=2), encoding="utf-8")
Path("nft_estimate.json").write_text(json.dumps(estimate_input, indent=2), encoding="utf-8")
