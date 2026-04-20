from pathlib import Path
import json
import random

random.seed(42)

root = Path('.')
(root / 'registry').mkdir(exist_ok=True)
(root / 'registry' / 'agents').mkdir(exist_ok=True)

agents = [
    {
        'name': 'security-auditor',
        'description': 'Analyzes code for security vulnerabilities and authentication flaws.',
        'path': 'registry/agents/security-auditor.md'
    },
    {
        'name': 'code-reviewer',
        'description': 'General code review and best practices with emphasis on readability.',
        'path': 'registry/agents/code-reviewer.md'
    },
    {
        'name': 'docs-helper',
        'description': 'Helps generate and polish documentation.',
        'path': 'registry/agents/docs-helper.md'
    },
    {
        'name': 'auth-debugger',
        'description': 'Troubleshoots authentication and session handling issues.',
        'path': 'registry/agents/auth-debugger.md'
    }
]

for agent in agents:
    p = root / agent['path']
    p.write_text(
        f"# {agent['name']}\n\nMARKER::{agent['name'].upper()}::42\n\n{agent['description']}\n",
        encoding='utf-8'
    )

manifest = {
    'version': 1,
    'agents': agents,
    'marker': 'REGISTRY_MARKER_ABC123'
}
(root / 'registry.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

(root / 'README_INPUT.txt').write_text(
    'Marker file for evaluation.\nExpected marker: REGISTRY_MARKER_ABC123\n',
    encoding='utf-8'
)
