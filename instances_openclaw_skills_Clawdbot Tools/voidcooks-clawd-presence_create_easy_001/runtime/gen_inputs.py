from pathlib import Path
import json

root = Path('.')
(root / 'notes').mkdir(exist_ok=True)
(root / 'notes' / 'marker.txt').write_text('marker: clawd-presence-task-001\nagent: NOVA\nletter: N\ntimeout: 600\n', encoding='utf-8')
(root / 'seed_data.json').write_text(json.dumps({'task_id': 'clawd-presence-task-001', 'expected_name_hint': 'NOVA', 'expected_letter_hint': 'N', 'expected_timeout': 600}, indent=2), encoding='utf-8')
