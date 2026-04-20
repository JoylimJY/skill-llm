from pathlib import Path
import json

# Deterministic sample input with a clear marker for evaluation
sample = {
    "observation_id": "BL-TEST-0007",
    "marker_name": "Hydrogen_Hole_Alpha",
    "classification_hint": "ANOMALY_FLAGGED",
    "score_hint": 0.87,
    "notes": "Synthetic benchmark payload for OpenSETI task generation."
}
Path("input.json").write_text(json.dumps(sample, indent=2), encoding="utf-8")
Path("marker.txt").write_text("MARKER: Hydrogen_Hole_Alpha\nCLASSIFICATION: ANOMALY_FLAGGED\nSCORE: 0.87\n", encoding="utf-8")
