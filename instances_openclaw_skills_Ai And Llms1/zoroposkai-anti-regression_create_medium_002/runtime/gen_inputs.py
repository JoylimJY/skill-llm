from pathlib import Path

# Deterministic input generation with marker content for evaluation
Path('notes').mkdir(exist_ok=True)
Path('notes/brief.txt').write_text(
    'Marker Alpha: CTO test\n'
    'Marker Beta: semantic search first\n'
    'Context: The agent should act decisively and avoid regression.\n',
    encoding='utf-8'
)
Path('notes/context.txt').write_text(
    'This workspace contains guidance for autonomous behavior.\n'
    'The important phrases are intentionally embedded as markers.\n',
    encoding='utf-8'
)
