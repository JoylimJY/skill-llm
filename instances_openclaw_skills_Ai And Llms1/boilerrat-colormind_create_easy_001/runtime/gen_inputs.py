from pathlib import Path
import json

# Deterministic input marker file
Path('task_marker.txt').write_text('COLORMIND_TASK_MARKER_2025_01\n', encoding='utf-8')

# Optional helper input for evaluation context
payload = {
    'project': 'landing-page-refresh',
    'style': 'modern-ui',
    'locked_color': [0, 122, 255],
    'slots': 5
}
Path('input_config.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
