from pathlib import Path
import json

root = Path('.')
(root / 'assets').mkdir(exist_ok=True)

(root / 'brief.txt').write_text(
    'Northstar Studio launch brief\n'
    'Marker: NORTHSTAR-LAUNCH-2025\n'
    'Deliver a README, release notes, and manifest JSON for launch assets.\n',
    encoding='utf-8'
)

(root / 'assets' / 'logos.txt').write_text(
    'Primary logo reference\nNORTHSTAR-LAUNCH-2025\nSecondary mark\n',
    encoding='utf-8'
)

manifest_seed = {
    'project': 'Northstar Studio',
    'marker': 'NORTHSTAR-LAUNCH-2025',
    'assets': ['README.md', 'release-notes.md', 'launch-manifest.json']
}
(root / 'starter_manifest.json').write_text(json.dumps(manifest_seed, indent=2), encoding='utf-8')
