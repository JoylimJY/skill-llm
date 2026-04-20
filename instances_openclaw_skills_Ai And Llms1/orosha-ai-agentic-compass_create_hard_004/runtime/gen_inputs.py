from pathlib import Path
import json

base = Path('.')
(base / 'memory').mkdir(exist_ok=True)
(base / 'logs').mkdir(exist_ok=True)

(base / 'memory' / '2026-01-31.md').write_text(
    '\n'.join([
        '# Daily Memory',
        'User asked to fix the export pipeline. [DONE] Investigated file parsing.',
        'Tool error: retry timeout on remote fetch.',
        'Proactive note: draft a local-only reflection plan.',
        'Marker: AXIS_COMPLETION_LOW',
        ''
    ]),
    encoding='utf-8'
)

(base / 'memory' / 'MEMORY.md').write_text(
    '\n'.join([
        '# Long-Term Memory',
        'Decision: keep all analysis local-only.',
        'Reminder: stop checking the API during peak hours.',
        'Marker: AXIS_TOOL_QUALITY_LOW',
        ''
    ]),
    encoding='utf-8'
)

(base / 'logs' / 'tool.log').write_text(
    '\n'.join([
        '2026-01-31T09:00:00Z ERROR timeout while querying gateway',
        '2026-01-31T09:05:00Z INFO retry scheduled',
        'Marker: LOG_TIMEOUT_001',
        ''
    ]),
    encoding='utf-8'
)

metadata = {
    'daily': 'memory/2026-01-31.md',
    'long': 'memory/MEMORY.md',
    'log': 'logs/tool.log',
    'markers': ['AXIS_COMPLETION_LOW', 'AXIS_TOOL_QUALITY_LOW', 'LOG_TIMEOUT_001']
}
(base / 'input_manifest.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
