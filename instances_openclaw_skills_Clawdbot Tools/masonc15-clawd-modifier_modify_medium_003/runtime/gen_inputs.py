from pathlib import Path
import json
import random

random.seed(1337)

workspace = Path('.')
workspace.mkdir(parents=True, exist_ok=True)

# Marker file used by eval to confirm the generated workspace is the expected one
marker = {
    "task_id": "clawd_modify_medium_001",
    "seed": 1337,
    "markers": [
        "CLAWD_MARKER_ALPHA",
        "CLAWD_MARKER_BETA",
        "CLAWD_MARKER_GAMMA"
    ]
}
(workspace / "task_marker.json").write_text(json.dumps(marker, indent=2), encoding="utf-8")

# Reference note with verifiable content
notes = [
    "Reference: original Clawd body color uses coral/orange tones.",
    "Reference marker: CLAWD_MARKER_ALPHA",
    "Reference marker: CLAWD_MARKER_BETA",
    "Reference marker: CLAWD_MARKER_GAMMA",
]
(workspace / "reference_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
