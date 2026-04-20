from pathlib import Path
import json
import os
import random

random.seed(1337)

workspace = Path('.')

# Marker files to make verification deterministic
(workspace / 'session_notes.txt').write_text(
    'MARKER_SESSION_ALPHA\nProject: Orion\nPriority: medium\n',
    encoding='utf-8'
)

(workspace / 'entity_seed.json').write_text(
    json.dumps({
        'people': [
            {'name': 'Avery Chen', 'role': 'engineer'},
            {'name': 'Mina Patel', 'role': 'product manager'}
        ],
        'facts': [
            {'text': 'The release window is Friday afternoon', 'tags': ['release', 'schedule']},
            {'text': 'The cache issue only appears on cold start', 'tags': ['bug', 'cache']},
            {'text': 'Customer escalation goes through support first', 'tags': ['process', 'support']}
        ],
        'lessons': [
            {'action': 'deployed a hotfix without smoke tests', 'context': 'release', 'outcome': 'negative', 'insight': 'Always run smoke tests before deployment'},
            {'action': 'documented rollback steps', 'context': 'incident response', 'outcome': 'positive', 'insight': 'Rollback runbooks reduce recovery time'}
        ]
    }, indent=2),
    encoding='utf-8'
)

(workspace / 'memory_target.txt').write_text(
    'TARGET_DB=./agent_memory.db\nMARKER_TARGET_BETA\n',
    encoding='utf-8'
)
