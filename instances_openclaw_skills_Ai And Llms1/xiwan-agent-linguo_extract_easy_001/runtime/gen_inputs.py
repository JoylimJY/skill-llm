from pathlib import Path
import json

root = Path('.')
(root / 'skill_bundle').mkdir(exist_ok=True)

skill_md = '''# Agent Lingua (👽语)
Canonical spec: https://clawhub.ai/xiwan/agent-linguo
Protocol name: agent-lingua
Version: 0.4.0
Security levels: P, B, E
Handshake example: 👽09|$j:eyJwcm90b2NvbCI6ImFnZW50LWxpbmd1YSJ9
'''
(root / 'skill_bundle' / 'SKILL.md').write_text(skill_md, encoding='utf-8')

meta = {
    'marker': 'AGENT_LINGUA_MARKER_7F3A',
    'expected_protocol': 'agent-lingua',
    'expected_version': '0.4.0',
    'expected_url': 'https://clawhub.ai/xiwan/agent-linguo'
}
(root / 'skill_bundle' / 'meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
