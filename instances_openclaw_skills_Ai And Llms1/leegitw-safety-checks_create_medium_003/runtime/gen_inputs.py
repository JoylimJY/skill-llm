from pathlib import Path
import yaml

root = Path('.')
(root / '.openclaw').mkdir(parents=True, exist_ok=True)
(root / '.claude').mkdir(parents=True, exist_ok=True)
(root / '.openclaw' / 'cache').mkdir(parents=True, exist_ok=True)
(root / 'output' / 'safety').mkdir(parents=True, exist_ok=True)

config = {
    'model': {
        'expected': 'anthropic-opus-4-5-20251101',
        'strict': True,
    },
    'fallbacks': {
        'model': ['primary-model', 'fallback-model', 'cached'],
        'storage': ['primary-path', 'backup-path'],
    },
}
(root / '.openclaw' / 'safety-checks.yaml').write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
(root / '.claude' / 'safety-checks.yaml').write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
(root / '.openclaw' / 'cache' / 'staleness.log').write_text(
    'marker: SAFETY-CHECKS-INPUT\n'
    'fresh_item,age_seconds=120\n'
    'stale_item,age_seconds=5400\n'
    'critical_item,age_seconds=9000\n',
    encoding='utf-8'
)
(root / '.openclaw' / 'safety-checks.lock').write_text('pid=999999\nmarker=LOCK-MARKER-42\n', encoding='utf-8')
(root / 'output' / 'safety' / 'temp-orphan.log').write_text('orphan temp marker: TEMP-777\n', encoding='utf-8')
