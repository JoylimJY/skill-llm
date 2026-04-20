from pathlib import Path

# Deterministic input generation with marker content
base = Path('.')
(base / 'session_notes.txt').write_text(
    'MARKER: NORTHSTAR_HANDOFF\n'
    'Project Northstar uses a staged rollout.\n'
    'Team preference: keep updates concise.\n'
    'Decision: use weekly status summaries.\n'
    'Insight: rollout risk is highest during integration.\n',
    encoding='utf-8'
)
(base / 'memory_plan.json').write_text(
    '{"project":"Northstar","facts":["staged rollout","concise updates","weekly status summaries"]}\n',
    encoding='utf-8'
)
