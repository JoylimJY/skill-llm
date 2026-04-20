import json
from pathlib import Path

marker = "NEAR_BATCH_MARKER_7F3A"

send_data = {
    "campaign": {
        "name": "Spring Outreach",
        "marker": marker
    },
    "recipients": [
        {"account": "alice.near", "amount": "1.5"},
        {"account": "bob.near", "amount": "0.5"},
        {"account": "carol.near", "amount": "2.25"}
    ]
}

nft_data = {
    "campaign": {
        "name": "Spring Outreach",
        "marker": marker
    },
    "transfers": [
        {"token_id": "123", "receiver": "alice.near", "contract": "nft.example.near"},
        {"token_id": "456", "receiver": "carol.near", "contract": "nft.example.near"}
    ]
}

Path("send_input.json").write_text(json.dumps(send_data, indent=2), encoding="utf-8")
Path("nft_input.json").write_text(json.dumps(nft_data, indent=2), encoding="utf-8")
Path("notes.txt").write_text(f"Campaign marker: {marker}\nUse this marker in the final output.\n", encoding="utf-8")
