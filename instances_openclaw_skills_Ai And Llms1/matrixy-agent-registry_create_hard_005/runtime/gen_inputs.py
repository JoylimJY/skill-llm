from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')
(root / 'registry').mkdir(exist_ok=True)
(root / 'agents').mkdir(exist_ok=True)

agents = [
    {
        'name': 'security-auditor',
        'description': 'Analyzes code for security vulnerabilities, auth flaws, and unsafe defaults.',
        'tags': ['security', 'audit', 'auth', 'vulnerability'],
        'instructions': 'Review authentication, secrets handling, dependency risks, and input validation.'
    },
    {
        'name': 'code-reviewer',
        'description': 'Performs general code review and highlights maintainability issues.',
        'tags': ['review', 'quality', 'style', 'maintainability'],
        'instructions': 'Check clarity, structure, edge cases, and test coverage.'
    },
    {
        'name': 'docs-curator',
        'description': 'Improves documentation, usage examples, and onboarding notes.',
        'tags': ['docs', 'readme', 'examples', 'onboarding'],
        'instructions': 'Make docs concise, accurate, and easy to follow.'
    }
]

for agent in agents:
    path = root / 'agents' / f"{agent['name']}.json"
    path.write_text(json.dumps(agent, indent=2), encoding='utf-8')

marker = {
    'marker_id': 'REGISTRY_MARKER_48271',
    'hint': 'search first, load on demand, never preload all agents'
}
(root / 'registry' / 'marker.json').write_text(json.dumps(marker, indent=2), encoding='utf-8')

readme = '''# Agent Registry Demo

This workspace demonstrates lazy agent discovery.

- Search first
- Load only the best match
- Do not preload all agents

Marker: REGISTRY_MARKER_48271
'''
(root / 'README.md').write_text(readme, encoding='utf-8')
