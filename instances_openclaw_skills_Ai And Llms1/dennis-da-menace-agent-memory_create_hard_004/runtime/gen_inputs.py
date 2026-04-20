from pathlib import Path
import json

root = Path('.')

files = {
    'session_01.txt': """Customer: Maya Chen\nCompany: Northstar Logistics\nIssue: recurring sync failures with the order pipeline\nTooling: Clawdbot, Slack, Postgres\nMarker: AM-MARKER-ALPHA-17\nNotes: prefers concise updates and early warning on failures.\n""",
    'session_02.txt': """Engineer note:\n- Root cause suspected: stale webhook credentials after rotation\n- Workaround: restart sync worker and refresh token cache\n- Lesson: credential rotation should trigger an immediate validation step\n- Marker: AM-MARKER-BETA-42\n""",
    'session_03.json': json.dumps({
        'project': 'Northstar order sync',
        'status': 'partially resolved',
        'open_items': ['confirm alerting', 'document token refresh procedure'],
        'marker': 'AM-MARKER-GAMMA-88',
        'entities': [
            {'name': 'Maya Chen', 'type': 'person', 'role': 'customer lead'},
            {'name': 'Northstar Logistics', 'type': 'organization', 'segment': 'logistics'},
            {'name': 'Postgres', 'type': 'tool', 'usage': 'database'},
        ]
    }, indent=2),
    'session_04.md': """## Retrospective\n\nPositive outcome: the team found that writing the symptom timeline into memory made triage faster.\nNegative outcome: one-off log snippets were too noisy and should not be stored as durable facts.\nLesson: keep memory entries short, tagged, and session-independent.\nMarker: AM-MARKER-DELTA-03\n""",
}

for name, content in files.items():
    Path(name).write_text(content, encoding='utf-8')
