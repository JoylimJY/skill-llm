from pathlib import Path
import json
import random

random.seed(42)

conversations = [
    {
        "id": "c1",
        "speaker": "Avery",
        "text": "Percept should track Project Orion. Nina said the client is Northstar Labs and the deadline is Friday.",
        "timestamp": "2025-04-21T09:15:00Z"
    },
    {
        "id": "c2",
        "speaker": "Jordan",
        "text": "Yes, and Marco works on Orion with Avery. We should mention the dashboard on port 8960.",
        "timestamp": "2025-04-21T10:00:00Z"
    },
    {
        "id": "c3",
        "speaker": "Nina",
        "text": "Northstar Labs approved the privacy settings update. Keep everything local in SQLite and LanceDB.",
        "timestamp": "2025-04-21T11:30:00Z"
    }
]

Path("conversations.json").write_text(json.dumps(conversations, indent=2), encoding="utf-8")
Path("marker.txt").write_text("MARKER:ORION-8960-LOCAL-ONLY\n", encoding="utf-8")
