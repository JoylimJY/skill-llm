from pathlib import Path
import json

base = Path('.')
(base / 'input').mkdir(exist_ok=True)

usage_log = {
    'project': 'token-guard-demo',
    'model': 'gemini-3-flash',
    'records': [
        {'ts': '2025-04-01T12:00:00Z', 'prompt': 'Summarize the quarterly report', 'tokens': 1200},
        {'ts': '2025-04-01T12:00:12Z', 'prompt': 'Summarize the quarterly report', 'tokens': 1200},
        {'ts': '2025-04-01T12:00:24Z', 'prompt': 'Summarize the quarterly report', 'tokens': 1200},
        {'ts': '2025-04-01T12:04:00Z', 'prompt': 'Translate the release notes to Chinese', 'tokens': 900},
        {'ts': '2025-04-01T12:05:00Z', 'prompt': 'Draft a short email reply', 'tokens': 400},
    ],
    'quota_limit': 10000,
    'window_seconds': 60,
    'duplicate_burst_threshold': 3,
    'marker': 'TG_MARKER_9f3a2c'
}

(base / 'input' / 'usage_log.json').write_text(json.dumps(usage_log, indent=2), encoding='utf-8')
(base / 'input' / 'notes.txt').write_text(
    'Marker: TG_MARKER_9f3a2c\nExpected report names: summary.txt and report.json\n',
    encoding='utf-8'
)
