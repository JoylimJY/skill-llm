import json
from pathlib import Path

Path('input').mkdir(exist_ok=True)
logs = {
    'app.log': """2025-03-14 10:00:01 INFO User login succeeded for alice
2025-03-14 10:00:02 DEBUG password=Summer2025! auth=ok
2025-03-14 10:00:03 WARN token: sk_live_ABC123XYZ789 used for request /checkout
2025-03-14 10:00:04 INFO session id=abc123 still active
""",
    'audit.log': """2025-03-14 11:00:01 INFO requested by bob
2025-03-14 11:00:02 INFO Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.example.payload
2025-03-14 11:00:03 ERROR secret_key=prod-SECRET-99887766 failed validation
"""
}
for name, content in logs.items():
    Path('input', name).write_text(content, encoding='utf-8')
marker = {'marker': 'KNOWN_MARKER_LOG_SANITIZE_42', 'files': list(logs.keys())}
Path('input', 'marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
