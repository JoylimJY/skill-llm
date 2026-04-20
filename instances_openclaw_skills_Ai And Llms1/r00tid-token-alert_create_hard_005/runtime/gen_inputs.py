from pathlib import Path
import json

base = Path('.')
(base / 'input').mkdir(exist_ok=True)

sample = {
    'session_id': 'TOKEN-ALERT-2025-05-MARKER',
    'limit': 200000,
    'used': 156000,
    'thresholds': [75, 90, 95],
    'note': 'MARKER_SESSION_SAMPLE_DO_NOT_REMOVE'
}
(base / 'input' / 'session.json').write_text(json.dumps(sample, indent=2), encoding='utf-8')
(base / 'input' / 'README_MARKER.txt').write_text(
    'Token Alert benchmark input marker: MARKER_SESSION_SAMPLE_DO_NOT_REMOVE\n',
    encoding='utf-8'
)
