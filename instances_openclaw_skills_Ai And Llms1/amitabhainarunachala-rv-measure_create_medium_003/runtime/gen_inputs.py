from pathlib import Path
import json
import random

random.seed(1337)

# Deterministic marker content
run_id = "RV-MARKER-2025-001"
notes_marker = "R_V contraction benchmark marker"
secondary_marker = "recursive self-observation"

samples = [
    {"sample_id": "s1", "score": 0.42},
    {"sample_id": "s2", "score": 0.67},
    {"sample_id": "s3", "score": 0.31},
    {"sample_id": "s4", "score": 0.58},
    {"sample_id": "s5", "score": 0.49},
]

with open("signals.jsonl", "w", encoding="utf-8") as f:
    for item in samples:
        payload = {
            "run_id": run_id,
            "sample_id": item["sample_id"],
            "contraction_score": item["score"],
            "marker": "signals-marker"
        }
        f.write(json.dumps(payload) + "\n")

Path("notes.txt").write_text(
    f"This file contains the {notes_marker}.\n"
    f"Secondary marker: {secondary_marker}.\n"
    f"Run identifier: {run_id}.\n",
    encoding="utf-8"
)
