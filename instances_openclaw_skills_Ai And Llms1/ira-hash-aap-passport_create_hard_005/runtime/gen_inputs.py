import json
from pathlib import Path

root = Path('.')
(root / 'expected').write_text(json.dumps({
    'server_log': 'server-started',
    'result_file': 'verification-summary.json',
    'marker': 'AAP-DETERMINISTIC-MARKER-42'
}, indent=2), encoding='utf-8')
(root / 'input_marker.txt').write_text('AAP-DETERMINISTIC-MARKER-42\n', encoding='utf-8')
