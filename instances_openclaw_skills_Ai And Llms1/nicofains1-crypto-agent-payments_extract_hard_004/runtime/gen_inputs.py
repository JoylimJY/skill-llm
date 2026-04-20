from pathlib import Path
import json

workspace = Path('.')

files = {
    'notes_a.txt': '''Random scratch notes.
Wallet label: staging-rewards-1
Chain: Base
Chain ID: 8453
Token: usdc
Amount: 1250.50
Recipient: 0x7e5F4552091A69125d5DfCb7b8C2659029395Bdf
Marker: ONLYSWAPS-CASE-BETA
''',
    'notes_b.txt': '''Payment memo
This file is intentionally noisy.
Wallet label: alpha-batch-9
Chain: arbitrum
Chain ID: 42161
Token: ETH
Amount: 2
Recipient: 0x1111111111111111111111111111111111111111
Marker: ONLYSWAPS-CASE-ALPHA
Extra line: approved for transfer.
''',
    'readme.md': '''# Workspace Notes

Use the alpha case file for the final summary.
'''
}

for name, content in files.items():
    (workspace / name).write_text(content, encoding='utf-8')

# Deterministic marker manifest for verification
manifest = {
    'markers': ['ONLYSWAPS-CASE-ALPHA', 'ONLYSWAPS-CASE-BETA'],
    'target_file': 'notes_b.txt'
}
(workspace / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
