from pathlib import Path
import json

# Deterministic marker content
workspace = Path('.')
marker = {
    'session_name': 'clawdbot-demo-session',
    'limit_tokens': 200000,
    'used_tokens': 156000,
    'thresholds': [25, 50, 75, 90, 95],
    'marker': 'TOKEN_ALERT_MARKER_V1'
}

(workspace / 'session_status.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
(workspace / 'notes.txt').write_text(
    'Session note\nMarker: TOKEN_ALERT_MARKER_V1\nStatus: high warning\n',
    encoding='utf-8'
)
