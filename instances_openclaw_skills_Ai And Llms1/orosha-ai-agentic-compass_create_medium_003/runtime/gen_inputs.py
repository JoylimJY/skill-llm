from pathlib import Path
from textwrap import dedent

base = Path('.')
(base / 'memory').mkdir(exist_ok=True)
(base / 'logs').mkdir(exist_ok=True)

(base / 'memory' / '2026-01-31.md').write_text(dedent('''
# Daily Memory — 2026-01-31

Marker: DAILY_MARKER_ALPHA_913

## Notes
- Started implementing OSINT Graph Analyzer [DONE]
- Retried gateway diagnostic after timeout
- Forgot to update skills-to-build prioritization list
- Proposed a proactive review of cron failures without being asked
''').strip() + '\n', encoding='utf-8')

(base / 'MEMORY.md').write_text(dedent('''
# Long-Term Memory

Marker: LONG_MEMORY_MARKER_BETA_274

## Decisions
- Avoid checking Moltbook API during peak hours
- Keep plans local-only and file-based
- Prefer concrete output over vague reflection
''').strip() + '\n', encoding='utf-8')

(base / 'logs' / 'tool-errors.log').write_text(dedent('''
2026-01-31T08:00:00Z timeout tool=cron-check code=504
2026-01-31T08:05:00Z error tool=osint-fetch code=ENETUNREACH
''').strip() + '\n', encoding='utf-8')
