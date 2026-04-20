from pathlib import Path
import json

base = Path('.')
(base / 'input').mkdir(exist_ok=True)
(base / 'output' / 'safety').mkdir(parents=True, exist_ok=True)

config = {
    'model': {
        'expected': 'anthropic-opus-4-5-20251101',
        'strict': True
    },
    'fallbacks': {
        'model': ['primary-model', 'fallback-model', 'cached-model'],
        'storage': ['primary-path', 'backup-path']
    },
    'cache': {
        'ttl_seconds': 3600,
        'stale_count_marker': 14
    },
    'session': {
        'state': 'clean',
        'lock': 'none'
    }
}
(base / 'input' / 'safety-checks.yaml').write_text(json.dumps(config, indent=2), encoding='utf-8')

(base / 'input' / 'markers.txt').write_text(
    '\n'.join([
        'MODEL_PIN=anthropic-opus-4-5-20251101',
        'FALLBACK_CHAIN=model>storage>memory',
        'STALE_CACHE_COUNT=14',
        'SESSION_STATE=CLEAN',
        'AUDIT_TOKEN=SAFE-DELTA-42'
    ]) + '\n',
    encoding='utf-8'
)

(base / 'input' / 'cache_inventory.json').write_text(json.dumps({
    'fresh_entries': 142,
    'stale_entries': 14,
    'critical_stale': 0,
    'sample_stale_keys': ['api_response_auth', 'user_preferences']
}, indent=2), encoding='utf-8')

(base / 'input' / 'session_state.json').write_text(json.dumps({
    'lock_file': '.openclaw/safety-checks.lock',
    'lock_owner': None,
    'temp_files': 0,
    'state': 'clean'
}, indent=2), encoding='utf-8')
