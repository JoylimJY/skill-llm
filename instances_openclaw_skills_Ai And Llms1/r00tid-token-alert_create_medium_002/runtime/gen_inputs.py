from pathlib import Path
import json

root = Path('.')
(root / 'input').mkdir(exist_ok=True)
marker = {
    'session_id': 'SESSION-ALERT-7842',
    'limit': 200000,
    'used': 156000,
    'thresholds': [25, 50, 75, 90, 95],
    'note': 'marker-token-alert-high-warning'
}
(root / 'input' / 'session_data.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
(root / 'input' / 'README_MARKER.txt').write_text('TOKEN_ALERT_MARKER_HIGH_WARNING\nSESSION-ALERT-7842\n', encoding='utf-8')
