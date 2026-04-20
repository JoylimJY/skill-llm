from pathlib import Path
import json
import random

random.seed(42)

text = (
    'At the end of the day, it is important to remember that our platform was built to help teams work faster and smarter. '
    'First, it can automate repetitive tasks, secondly, it provides clear visibility into progress, and finally, it enables better collaboration across departments. '
    'I hope this helps, and let me know if you have any questions.'
)

Path('input.txt').write_text(text, encoding='utf-8')
Path('marker.json').write_text(json.dumps({'marker': 'HUMANIZE_TASK_MARKER_8427', 'seed': 42}, indent=2), encoding='utf-8')
