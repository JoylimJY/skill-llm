from pathlib import Path
import json

workspace = Path('.')
config = {
    'chainId': 8453,
    'network': 'base',
    'task': 'wallet_readiness_check',
    'marker': 'ONLYSWAPS_READY_2025_03_01'
}
Path('input_config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')
Path('README_TASK.txt').write_text(
    'Marker: ONLYSWAPS_READY_2025_03_01\n'
    'Expected chain: Base (8453)\n'
    'Expected action: wallet readiness check\n',
    encoding='utf-8'
)
