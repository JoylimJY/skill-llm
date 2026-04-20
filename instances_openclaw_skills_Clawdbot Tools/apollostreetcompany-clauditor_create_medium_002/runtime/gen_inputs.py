from pathlib import Path
import json

root = Path('.')
(root / 'input_manifest.json').write_text(json.dumps({
    'marker': 'CLAUDITOR_TEST_MARKER_7F3A',
    'expected_log_name': 'events.log',
    'expected_key_name': 'key'
}, indent=2), encoding='utf-8')

(root / 'events.log').write_text(
    '2025-04-01T10:00:00Z INFO marker=CLAUDITOR_TEST_MARKER_7F3A action=login user=alice\n'
    '2025-04-01T10:05:00Z WARN marker=CLAUDITOR_TEST_MARKER_7F3A action=file_access path=/tmp/report.txt\n',
    encoding='utf-8'
)

(root / 'key').write_text('test-key-CLAUDITOR_TEST_MARKER_7F3A\n', encoding='utf-8')
