from pathlib import Path
import json

# Deterministic input marker file for the task
content = {
    "model_name": "simple_gear",
    "teeth": 12,
    "center_hole_radius_mm": 3,
    "marker": "GEAR_INPUT_MARKER_2025"
}
Path("input.json").write_text(json.dumps(content, indent=2), encoding="utf-8")
