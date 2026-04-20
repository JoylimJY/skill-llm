from pathlib import Path

root = Path('.')
mem = root / 'memory'
mem.mkdir(exist_ok=True)

(root / 'MEMORY.md').write_text(
    '# MEMORY\n\n'
    '- [DONE] Fixed the CI retry loop issue.\n'
    '- Mentioned that tool timeouts were happening during peak hours.\n'
    '- Noted a desire to improve proactive planning.\n',
    encoding='utf-8'
)

(mem / '2026-01-31.md').write_text(
    '# Daily Memory\n\n'
    '- [DONE] Completed the logging cleanup.\n'
    '- [TODO] Draft a better agent action plan.\n'
    '- Tool error log: timeout while calling external parser.\n'
    '- Marker: AGENTIC_COMPASS_INPUT_READY\n',
    encoding='utf-8'
)

(root / 'logs.txt').write_text(
    '2026-01-31 09:00 failed tool call: timeout\n'
    '2026-01-31 09:05 recovered after retry\n',
    encoding='utf-8'
)
