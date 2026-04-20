from pathlib import Path
import json
import random

random.seed(1337)

# Marker file to verify task inputs
meta = {
    "task": "clawd_modifier",
    "markers": ["CLAWD_BLUE_ARMS", "EXPECTED_SMALL_ART", "EXPECTED_COLOR_CHANGE"],
    "seed": 1337,
}
Path("task_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

# Reference note for the assistant, deterministic and marker-rich
note = (
    "Task marker: CLAWD_BLUE_ARMS\n"
    "Target: change clawd_body to a blue preset and add both arms.\n"
    "Expected small art style: preserve the mascot layout, only modify color/art.\n"
    "Verification marker: EXPECTED_COLOR_CHANGE\n"
)
Path("instructions.txt").write_text(note, encoding="utf-8")

# Create a tiny manifest with deterministic pseudo-random values for robustness checks
values = [random.randint(10, 99) for _ in range(5)]
Path("manifest.csv").write_text("key,value\n" + "\n".join([f"m{i},{v}" for i, v in enumerate(values)]), encoding="utf-8")
