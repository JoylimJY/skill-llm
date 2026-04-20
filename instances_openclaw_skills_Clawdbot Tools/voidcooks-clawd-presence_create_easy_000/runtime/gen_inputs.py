from pathlib import Path
import json

config = {
    "letter": "B",
    "name": "BETA",
    "idle_timeout": 300,
    "marker": "INPUT_MARKER_47A9"
}

Path("config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
Path("notes.txt").write_text("Deterministic marker: INPUT_MARKER_47A9\n", encoding="utf-8")
