import os
from pathlib import Path
import json
import random

random.seed(1337)
base = Path('.')
base.mkdir(parents=True, exist_ok=True)

corpus = {
    'aurora_notes.txt': [
        'MARKER:AURORA_PROJECT',
        'Project codename: Aurora Relay',
        'Goal: build a lightweight incident relay for on-call teams.',
        'Constraint: the first release must support offline mode.',
        'Decision: ship with a message queue instead of direct sync.',
        'Insight: deterministic fixtures make queue replay tests stable.',
    ],
    'release_brief.txt': [
        'MARKER:RELEASE_BRIEF',
        'Audience: support engineers and SREs.',
        'Success metric: shorten incident handoff time.',
        'Do not store secrets or credentials in memory notes.',
    ],
    'scratchpad.json': {
        'marker': 'MARKER:SCRATCHPAD',
        'seed': 1337,
        'labels': ['offline', 'queue', 'deterministic', 'semantic-link', 'causal-link']
    }
}

for name, content in corpus.items():
    p = base / name
    if isinstance(content, list):
        p.write_text('\n'.join(content) + '\n', encoding='utf-8')
    else:
        p.write_text(json.dumps(content, indent=2, sort_keys=True) + '\n', encoding='utf-8')
