import json
from pathlib import Path

payload = {
    "recipients": [
        {"account": "bob.near", "amount": "1.5"},
        {"account": "carol.near", "amount": "0.5"}
    ]
}
Path("recipients.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
Path("marker.txt").write_text("NEAR_BATCH_MARKER_7F3A1C", encoding="utf-8")
