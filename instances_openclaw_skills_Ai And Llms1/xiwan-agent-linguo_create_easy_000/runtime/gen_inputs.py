from pathlib import Path
import base64, json

workspace = Path('.')
# Deterministic marker input for verification
marker = {
    'task': 'agent-lingua-handshake',
    'marker': 'ALPHA-4242',
    'supported': ['P', 'B', 'E']
}
Path('input_marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')
# Additional deterministic hint file
payload = json.dumps({'hint': 'include signature and base64 payload', 'id': 'ALPHA-4242'}, separators=(',', ':')).encode('utf-8')
Path('input_hint.b64').write_text(base64.b64encode(payload).decode('ascii'), encoding='utf-8')
