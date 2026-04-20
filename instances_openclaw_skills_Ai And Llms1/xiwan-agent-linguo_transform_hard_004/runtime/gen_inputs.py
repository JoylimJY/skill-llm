from pathlib import Path
import json
import random

random.seed(742913118)

root = Path('.')
(root / 'inputs').mkdir(exist_ok=True)

source = {
    'marker_alpha': 'MARKER_ALPHA_742',
    'marker_beta': 'MARKER_BETA_913',
    'marker_gamma': 'MARKER_GAMMA_118',
    'version': '0.4.0',
    'canonical_url': 'https://clawhub.ai/xiwan/agent-linguo',
    'signature': '--👽lingua/[version]@[source]',
    'security_levels': ['P', 'B', 'E'],
    'handshake_domain_action': '👽09',
    'field_examples': {'t': 'title', 'c': 'content', 'ts': 'timestamp', 'ui': 'userId'}
}

(root / 'inputs' / 'protocol_source.json').write_text(json.dumps(source, indent=2), encoding='utf-8')

md = f'''# Agent Lingua Source Notes

Canonical URL: {source['canonical_url']}
Version: {source['version']}
Signature: {source['signature']}
Handshake: {source['handshake_domain_action']}
Security: {', '.join(source['security_levels'])}

Known markers:
- {source['marker_alpha']}
- {source['marker_beta']}
- {source['marker_gamma']}

Field mapping samples:
- t = title
- c = content
- ts = timestamp
- ui = userId
'''
(root / 'inputs' / 'source_notes.md').write_text(md, encoding='utf-8')
