from pathlib import Path
import json

root = Path('.')
marker = {
    "generated": True,
    "marker": "OPENCLAW_TASK_MARKER_7F3A",
    "note": "Deterministic input seed fixed"
}
(root / 'input_marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
