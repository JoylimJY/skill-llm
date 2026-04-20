from pathlib import Path
import json

workspace = Path('.')

notes = {
    'project_alpha.txt': (
        'PROJECT: Alpha Search\n'
        'OWNER: Mira Patel\n'
        'STACK: Python 3.11, SQLite, FastAPI\n'
        'KNOWN_FACT: The agent memory database should persist across sessions.\n'
        'ENTITY: Mira Patel | person | role=product owner\n'
    ),
    'project_beta.txt': (
        'PROJECT: Beta Sync\n'
        'OWNER: Jonah Reed\n'
        'STACK: Node 20, Redis, background jobs\n'
        'KNOWN_FACT: Lessons learned should be recorded after failures.\n'
        'ENTITY: Jonah Reed | person | role=backend engineer\n'
    ),
    'session_log.txt': (
        'SESSION_START\n'
        'ACTION: Tried to recall recent context before making changes.\n'
        'OUTCOME: negative\n'
        'INSIGHT: Loading recent lessons first helps avoid repeating the same mistake.\n'
        'FACT: The database path is ~/.agent-memory/memory.db by default.\n'
    ),
}

for name, content in notes.items():
    Path(name).write_text(content, encoding='utf-8')

# Marker file for deterministic verification by the evaluator
Path('marker.json').write_text(json.dumps({'marker': 'AGENT_MEMORY_TASK_V1', 'files': sorted(notes.keys())}, indent=2), encoding='utf-8')
