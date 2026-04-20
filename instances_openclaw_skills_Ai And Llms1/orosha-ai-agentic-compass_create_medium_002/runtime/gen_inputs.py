from pathlib import Path

BASE = Path('.')
mem = BASE / 'memory'
mem.mkdir(exist_ok=True)

# Deterministic marker-rich inputs
(mem / '2026-01-31.md').write_text(
    '\n'.join([
        '# Daily Memory 2026-01-31',
        'User asked for a concise agent plan.',
        '[DONE] Finished drafting the API summary.',
        'Tool error log: retry timeout on local parser once.',
        'Proactive note: start OSINT Graph Analyzer implementation.',
        'Avoidance note: do not check Moltbook API during peak hours.',
        'Reference: previous decision to write output into memory/agentic-compass.md.',
        'MARKER_DAILY_ALPHA_17',
    ])
    + '\n',
    encoding='utf-8'
)

(mem / 'MEMORY.md').write_text(
    '\n'.join([
        '# Long-Term Memory',
        'Completed tasks are tracked with [DONE] markers.',
        'Remember to produce one proactive, one deferred, one avoidance, and one ship item.',
        'Last weak axis observed: Completion Rate due to unfinished follow-ups.',
        'Tool logs sometimes mention gateway diagnostic retries.',
        'MARKER_LONG_BETA_42',
    ])
    + '\n',
    encoding='utf-8'
)

# Extra file to ensure the workspace has multiple local-only sources
(mem / 'notes.txt').write_text(
    'initiative=high\nconsistency=medium\nrelevance=high\nMARKER_NOTES_GAMMA_08\n',
    encoding='utf-8'
)
