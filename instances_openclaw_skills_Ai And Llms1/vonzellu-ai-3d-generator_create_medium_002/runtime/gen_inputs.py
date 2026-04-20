from pathlib import Path
import json

Path('input').mkdir(exist_ok=True)
marker = {
    'model_name': 'ember_keep',
    'marker_text': 'MK-3D-4827',
    'style': 'medieval tower',
    'base_size_mm': [48, 48, 6],
    'tower_height_mm': 72,
    'detail_level': 'medium'
}
Path('input/marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
Path('input/description.txt').write_text(
    'Design a 3D printable medieval tower with a square base, four corner turrets, crenellations,\n'
    'a pointed roof, and a small embossed plaque containing the marker text.',
    encoding='utf-8'
)
