from pathlib import Path
from datetime import date
import json

base = Path('.')
(base / 'references').mkdir(exist_ok=True)
(base / 'memory').mkdir(exist_ok=True)

(base / 'references' / 'openclaw-workspace.md').write_text('# marker: workspace reference\n', encoding='utf-8')
(base / 'references' / 'templates.md').write_text('# marker: templates reference\n', encoding='utf-8')
(base / 'references' / 'architecture.md').write_text('# marker: architecture reference\n', encoding='utf-8')

marker_date = date(2025, 5, 1).isoformat()
(base / 'memory' / f'{marker_date}.md').write_text(
    '## Seed\n- marker: agent created\n- project: OpsLighthouse\n',
    encoding='utf-8'
)

(base / 'workspace_request.json').write_text(
    json.dumps({
        'agent_name': 'OpsLighthouse',
        'user_name': 'Team Lead',
        'timezone': 'UTC',
        'channels': ['Telegram', 'Discord'],
        'tone': 'professional, calm, concise',
        'autonomy': 'Operator',
        'memory': ['common requests', 'escalation boundaries', 'daily triage'],
    }, indent=2),
    encoding='utf-8'
)
