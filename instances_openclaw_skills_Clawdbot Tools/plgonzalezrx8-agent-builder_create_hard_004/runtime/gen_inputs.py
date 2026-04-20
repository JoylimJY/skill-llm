from pathlib import Path
from datetime import date

root = Path('.')
root.mkdir(parents=True, exist_ok=True)

today = date.today().isoformat()

# Marker file to help the evaluator verify the generated workspace was seeded.
(root / 'INPUT_MARKER.txt').write_text(
    'MARKER:OPENCLAW-CLAWPILOT-SEED\nDATE:' + today + '\n',
    encoding='utf-8'
)

# Create a tiny context note used by the task description.
(root / 'context.json').write_text(
    '{"agent_name":"ClawPilot","user_name":"Mira","timezone":"Asia/Singapore"}',
    encoding='utf-8'
)
