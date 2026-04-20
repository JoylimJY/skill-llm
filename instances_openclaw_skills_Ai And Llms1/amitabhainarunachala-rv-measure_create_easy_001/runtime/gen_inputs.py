from pathlib import Path
import json
import random

random.seed(42)
base = Path('.')
(base / 'data').mkdir(exist_ok=True)
items = {
    'model_name': 'rv-demo-small',
    'measurements': [0.18, 0.21, 0.19, 0.22],
    'marker': 'RV-CONTRACTION-OK'
}
(base / 'data' / 'sample.json').write_text(json.dumps(items, indent=2), encoding='utf-8')
