from pathlib import Path
import json

base = Path('.')
(base / 'memory').mkdir(exist_ok=True)
(base / 'logs').mkdir(exist_ok=True)

(base / 'memory' / '2026-01-31.md').write_text(
    '# Daily Memory\n\n'
    '- [DONE] Fixed parser edge case in the Agentic Compass prototype.\n'
    '- [DONE] Drafted a ship plan for memory consistency tracking.\n'
    '- [TODO] Review tool error logs for repeated retries.\n'
    '- [NOTE] Marker: ACOMPASS-DAILY-31\n',
    encoding='utf-8'
)

(base / 'memory' / 'MEMORY.md').write_text(
    '# Long Memory\n\n'
    '- Prior decision: prioritize objective metrics over subjective self-assessment.\n'
    '- Prior decision: avoid using network calls for local-only reflection tools.\n'
    '- Forgotten pattern: tool retries spike after malformed input files.\n'
    '- Marker: ACOMPASS-LONG-77\n',
    encoding='utf-8'
)

(base / 'logs' / 'tool-errors.log').write_text(
    '2026-01-31T10:00:00Z ERROR retry timeout on fetch_plan\n'
    '2026-01-31T10:02:00Z ERROR malformed markdown in memory/2026-01-31.md\n'
    'Marker: ACOMPASS-LOG-ERROR-12\n',
    encoding='utf-8'
)

meta = {
    'seed': 12345,
    'markers': {
        'daily': 'ACOMPASS-DAILY-31',
        'long': 'ACOMPASS-LONG-77',
        'log': 'ACOMPASS-LOG-ERROR-12'
    }
}
(base / 'input_manifest.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
