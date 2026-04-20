import json
from pathlib import Path

base = Path('.')
(base / 'inputs').mkdir(exist_ok=True)

conversations = [
    {
        'filename': 'inputs/conv_alpha.txt',
        'marker': 'MARKER-ALPHA-4817',
        'text': '2025-04-10 Team chat\n\nAlice said the Nimbus migration should finish before Friday. Bob agreed to keep the API stable. They noted that Project Orion depends on the migration, and Alice will send a short update to Carol. Decision: keep Nimbus on the current release branch for now.'
    },
    {
        'filename': 'inputs/conv_beta.txt',
        'marker': 'MARKER-BETA-9021',
        'text': '2025-04-11 Notes from the hallway\n\nCarol mentioned that Project Orion needs an extra review pass. Dan volunteered to check the rollout checklist. Decision: postpone the launch until the review is complete. Bob and Carol will sync again on Monday.'
    },
    {
        'filename': 'inputs/conv_gamma.txt',
        'marker': 'MARKER-GAMMA-1144',
        'text': '2025-04-12 Voice memo transcript\n\nAlice, Dan, and Bob discussed the Atlas prototype. Atlas is separate from Orion but shares the same metrics dashboard. Decision: Alice will own the prototype notes, and Dan will collect feedback from the design team.'
    }
]

for item in conversations:
    Path(item['filename']).write_text(f"{item['marker']}\n{item['text']}\n", encoding='utf-8')

manifest = {
    'bundle_name': 'percept_bundle',
    'inputs': [
        {'filename': item['filename'], 'marker': item['marker']} for item in conversations
    ],
    'expected_outputs': ['percept_bundle/entities.json', 'percept_bundle/summary.txt']
}
Path('inputs/manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
