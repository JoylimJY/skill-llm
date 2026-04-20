from pathlib import Path
import json

# Deterministic input marker file for the task
marker = {
    "task_id": "colormind_easy_001",
    "base_color": [0, 122, 255],
    "models": ["default", "ui"]
}
Path("task_input.json").write_text(json.dumps(marker, indent=2), encoding="utf-8")
