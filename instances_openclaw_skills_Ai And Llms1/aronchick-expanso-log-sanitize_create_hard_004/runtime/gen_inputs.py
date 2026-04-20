from pathlib import Path
import json

base = Path('.')
files = {
    'app.log': '''2025-04-18T09:15:01Z INFO user=alice action=login status=ok
2025-04-18T09:15:02Z WARN password=superSecret123 failed_attempt=1
2025-04-18T09:15:03Z INFO token=ghp_ABC123xyz789SECRET987654321 data synced
2025-04-18T09:15:04Z DEBUG request_id=req-001 message=heartbeat
''',
    'service.log': '''[2025-04-18 09:16:10] INFO bearer=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.x.y connected
[2025-04-18 09:16:11] INFO session_id=SID-4f8a2c1d-9f3e-4b2f-9b2a-111122223333 cache=warm
[2025-04-18 09:16:12] ERROR detail=timeout endpoint=/v1/items
''',
    'notes.log': '''plain text line without secrets
another line with api_key=sk_test_51NfExampleMarker000000000000
final line with secret: top-secret-value
'''
}
for name, content in files.items():
    (base / name).write_text(content, encoding='utf-8')

# Marker file to help evaluation confirm deterministic generation context
marker = {
    'marker': 'LOG-SANITIZE-2025-04',
    'inputs': sorted(files.keys()),
    'expected_output': 'sanitized.log'
}
(base / 'input_manifest.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
