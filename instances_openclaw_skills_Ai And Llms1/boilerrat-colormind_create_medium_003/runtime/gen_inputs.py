import json
from pathlib import Path

# Deterministic seed marker content for eval
marker = {
    "project": "fintech-dashboard",
    "brand_color_rgb": [0, 122, 255],
    "expected_model_hint": "ui",
    "token": "COLORMIND_MARKER_2025_04"
}
Path('input_marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')

Path('notes.txt').write_text(
    'Task marker: COLORMIND_MARKER_2025_04\n'
    'Use model ui and lock the brand color 0,122,255.\n',
    encoding='utf-8'
)
