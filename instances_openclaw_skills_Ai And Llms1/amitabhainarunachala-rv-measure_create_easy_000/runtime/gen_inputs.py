from pathlib import Path
import json
import random

random.seed(42)
base = Path('.')
(base / 'data').mkdir(exist_ok=True)

# Create deterministic input files with marker content
files = {
    'data/input_a.txt': 'rv-measure marker: AIKAGRYA_RV_CONTRACTION\nalpha=12\nbeta=34\n',
    'data/input_b.txt': 'notes\nThis file also contains the marker AIKAGRYA_RV_CONTRACTION in plain text.\n',
    'data/config.json': json.dumps({'skill': 'rv-measure', 'marker': 'AIKAGRYA_RV_CONTRACTION', 'threshold': 0.5}, indent=2),
}

for rel, content in files.items():
    path = base / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
