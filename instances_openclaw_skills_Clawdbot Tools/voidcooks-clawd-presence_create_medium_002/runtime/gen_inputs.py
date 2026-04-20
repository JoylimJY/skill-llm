from pathlib import Path
import json

root = Path('.')
assets = root / 'assets' / 'monograms'
assets.mkdir(parents=True, exist_ok=True)

# Deterministic marker monogram content
(root / 'assets' / 'monograms' / 'Q.txt').write_text(
    'QQQQQ\nQ   Q\nQ Q Q\nQ   Q\nQQQQQ\n',
    encoding='utf-8'
)

# Marker config hint file for evaluation
(root / 'input_marker.json').write_text(
    json.dumps({
        'marker': 'clawd-presence-eval',
        'expected_letter': 'Q',
        'expected_name': 'QUARTZ',
        'expected_timeout': 420
    }, indent=2),
    encoding='utf-8'
)
