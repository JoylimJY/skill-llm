import json
import os
from pathlib import Path


def main():
    root = Path('.')
    agents_dir = root / '.claude' / 'agents'
    registry_dir = root / '.claude' / 'skills' / 'agent-registry'
    agents_dir.mkdir(parents=True, exist_ok=True)
    registry_dir.mkdir(parents=True, exist_ok=True)

    marker = 'MARKER_AGENT_REGISTRY_DEMO_9f3c2a'

    agents = [
        {
            'name': 'security-auditor',
            'version': '1.0.0',
            'description': 'Analyzes code for security vulnerabilities, authentication flaws, and risky patterns.',
            'keywords': ['security', 'auth', 'authentication', 'audit', 'review'],
            'priority': 0.92,
        },
        {
            'name': 'code-reviewer',
            'version': '1.0.0',
            'description': 'General code review assistant for style, correctness, and maintainability.',
            'keywords': ['review', 'code', 'quality'],
            'priority': 0.68,
        },
        {
            'name': 'docs-librarian',
            'version': '1.0.0',
            'description': 'Maintains documentation and examples across the repository.',
            'keywords': ['docs', 'documentation', 'examples'],
            'priority': 0.31,
        },
    ]

    # Deterministic source files
    for agent in agents:
        path = agents_dir / f"{agent['name']}.md"
        content = (
            f"---\n"
            f"name: {agent['name']}\n"
            f"version: {agent['version']}\n"
            f"description: {agent['description']}\n"
            f"keywords: {', '.join(agent['keywords'])}\n"
            f"marker: {marker}\n"
            f"---\n\n"
            f"# {agent['name']}\n\n"
            f"This agent focuses on: {', '.join(agent['keywords'])}.\n"
        )
        path.write_text(content, encoding='utf-8')

    # Create a registry index with stable ordering and score hints
    index = {
        'marker': marker,
        'registry_name': 'agent-registry',
        'agents': [
            {
                'name': a['name'],
                'description': a['description'],
                'keywords': a['keywords'],
                'score_hint': a['priority'],
                'source_file': f".claude/agents/{a['name']}.md",
            }
            for a in agents
        ],
    }
    (registry_dir / 'registry.json').write_text(json.dumps(index, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    # Add a lightweight README to make the registry feel complete
    readme = (
        '# agent-registry\n\n'
        f'Generated demo registry. Marker: {marker}\n\n'
        'Use search-first discovery to find the best matching agent.\n'
    )
    (registry_dir / 'README.md').write_text(readme, encoding='utf-8')


if __name__ == '__main__':
    main()
