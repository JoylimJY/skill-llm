import json
from pathlib import Path

# Deterministic input generation with embedded markers
base = Path('.')
base.mkdir(parents=True, exist_ok=True)

config = {
    "marker_name": "RV_MARKER_ALPHA",
    "threshold": 0.42,
    "observations": [0.18, 0.26, 0.31, 0.47, 0.52]
}
(base / 'input_config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')

(base / 'observations.csv').write_text(
    "step,value,marker\n"
    "1,0.18,RV_MARKER_ALPHA\n"
    "2,0.26,RV_MARKER_ALPHA\n"
    "3,0.31,RV_MARKER_ALPHA\n"
    "4,0.47,RV_MARKER_ALPHA\n"
    "5,0.52,RV_MARKER_ALPHA\n",
    encoding='utf-8'
)

(base / 'notes.txt').write_text(
    "Reference marker: RV_MARKER_ALPHA\n"
    "Expected threshold: 0.42\n"
    "This file is deterministic and intended for eval verification.\n",
    encoding='utf-8'
)
