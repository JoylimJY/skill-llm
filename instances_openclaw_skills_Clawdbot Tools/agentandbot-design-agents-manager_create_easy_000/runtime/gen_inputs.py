from pathlib import Path
import json

# Deterministic input generation with embedded markers
workspace = Path('.')
(workspace / 'input_registry.json').write_text(json.dumps({
    'agents': [
        {'id': 'main', 'name': 'Clawdia', 'status': 'Healthy', 'reports_to': 'Ilkerkaan'}
    ],
    'marker': 'AGENT_MARKER_001'
}, indent=2), encoding='utf-8')

(workspace / 'notes.txt').write_text(
    'Reference marker: AGENT_MARKER_001\nMain agent is Clawdia and is Healthy.\n',
    encoding='utf-8'
)
