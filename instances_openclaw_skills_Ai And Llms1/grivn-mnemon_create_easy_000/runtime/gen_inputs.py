from pathlib import Path
import json

base = Path('.')
(base / 'inputs').mkdir(exist_ok=True)

marker = 'MNEMON_MARKER_ALPHA_2025'
files = {
    'inputs/memory1.txt': f'Project preference: use the default store for quick notes.\nMarker: {marker}\n',
    'inputs/memory2.txt': f'Decision note: link closely related memories with semantic edges.\nMarker: {marker}\n',
    'inputs/memory3.txt': f'Context: this workspace is for a small mnemon demo task.\nMarker: {marker}\n',
}
for rel, content in files.items():
    Path(rel).write_text(content, encoding='utf-8')

manifest = {
    'marker': marker,
    'files': list(files.keys()),
}
Path('inputs/manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
