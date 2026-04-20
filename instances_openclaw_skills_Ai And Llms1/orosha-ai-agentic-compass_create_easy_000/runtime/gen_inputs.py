from pathlib import Path

base = Path('.')
mem = base / 'memory'
mem.mkdir(exist_ok=True)

(base / 'MEMORY.md').write_text(
    '# Long-term Memory\n\n'
    '- [DONE] Finish weekly report\n'
    '- [DONE] Review tool logs\n'
    '- Remember to avoid peak-hour API checks\n'
    '- Plan to draft a prioritization document\n',
    encoding='utf-8'
)

(mem / '2026-01-31.md').write_text(
    '# Daily Memory 2026-01-31\n\n'
    '- [DONE] Start first implementation of OSINT Graph Analyzer\n'
    '- Tool error: timeout while calling gateway diagnostic\n'
    '- User asked about memory consistency and next steps\n'
    '- Marker: AGENTIC_COMPASS_INPUT_V1\n',
    encoding='utf-8'
)
