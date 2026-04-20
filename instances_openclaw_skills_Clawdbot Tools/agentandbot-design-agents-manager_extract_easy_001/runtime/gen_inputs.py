from pathlib import Path

base = Path('.')
(base / 'references').mkdir(exist_ok=True)

registry = '''# Agent Registry

*Last updated: 2026-01-31T17:55Z*

## Agent List

| ID | Name | Model | Reports To | Can Assign To | Last Updated |
|----|------|-------|------------|---------------|--------------|
| main | Clawdia | glm-4.7 | Ilkerkaan (human) | TBD (sub-agents on-demand) | 2026-01-31 |
'''
(base / 'references' / 'agent-registry.md').write_text(registry, encoding='utf-8')

marker = 'MARKER_ROUTING_SUMMARY_INPUT_9F3A'
(base / 'input_marker.txt').write_text(marker + '\n', encoding='utf-8')
