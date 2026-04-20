from pathlib import Path
import json

base = Path('.')
(base / '.openclaw').mkdir(exist_ok=True)
(base / '.claude').mkdir(exist_ok=True)
(base / '.openclaw' / 'cache').mkdir(parents=True, exist_ok=True)
(base / 'output' / 'safety').mkdir(parents=True, exist_ok=True)

config = {
    'model': {
        'expected': 'anthropic-opus-4-5-20251101',
        'strict': True
    },
    'fallbacks': {
        'model': ['primary-model', 'fallback-model', 'cached'],
        'storage': ['primary-path', 'backup-path']
    }
}

(base / '.openclaw' / 'safety-checks.yaml').write_text(
    'model:\n  expected: "anthropic-opus-4-5-20251101"\n  strict: true\nfallbacks:\n  model:\n    - primary-model\n    - fallback-model\n    - cached\n  storage:\n    - primary-path\n    - backup-path\n',
    encoding='utf-8'
)

(base / '.claude' / 'safety-checks.yaml').write_text(
    'fallbacks:\n  model:\n    - backup-a\n    - backup-b\n',
    encoding='utf-8'
)

marker = {
    'marker': 'SAFETY-CHECKS-BASELINE-2025-05',
    'ttl_seconds': 3600,
    'cache_entries': [
        {'name': 'fresh_alpha', 'age_seconds': 1200},
        {'name': 'stale_beta', 'age_seconds': 5400},
        {'name': 'stale_gamma', 'age_seconds': 8100}
    ],
    'session': {
        'lock_file': '.openclaw/safety-checks.lock',
        'temp_files': ['output/safety/temp-leak-1.log', 'output/safety/temp-leak-2.log']
    }
}

(base / '.openclaw' / 'cache' / 'staleness.log').write_text(json.dumps(marker, indent=2), encoding='utf-8')

(base / '.openclaw' / 'safety-checks.lock').write_text('PID 99999\nOWNER test\n', encoding='utf-8')
(base / 'output' / 'safety' / 'temp-leak-1.log').write_text('temporary data A\n', encoding='utf-8')
(base / 'output' / 'safety' / 'temp-leak-2.log').write_text('temporary data B\n', encoding='utf-8')
