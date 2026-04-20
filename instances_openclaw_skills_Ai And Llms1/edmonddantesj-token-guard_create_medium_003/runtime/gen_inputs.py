import json
from pathlib import Path

root = Path('.')
(root / 'inputs').mkdir(exist_ok=True)

config = {
    'models': {
        'gemini-3-flash': {'tpm_limit': 1000000, 'soft_limit_pct': 80, 'hard_limit_pct': 95},
        'claude-sonnet': {'tpm_limit': 200000, 'soft_limit_pct': 80, 'hard_limit_pct': 95}
    },
    'duplicate_window_seconds': 60,
    'cache_enabled': True
}
(root / 'inputs' / 'config.json').write_text(json.dumps(config, indent=2), encoding='utf-8')

prompts = [
    {'id': 'req-001', 'model': 'gemini-3-flash', 'text': 'Hello world marker ALPHA 123.'},
    {'id': 'req-002', 'model': 'gemini-3-flash', 'text': 'Hello world marker ALPHA 123.'},
    {'id': 'req-003', 'model': 'claude-sonnet', 'text': 'CJK marker: 你好，世界。BETA-456'},
    {'id': 'req-004', 'model': 'claude-sonnet', 'text': 'Unique request GAMMA_789 with enough length to test estimation.'}
]
(root / 'inputs' / 'prompts.json').write_text(json.dumps(prompts, indent=2, ensure_ascii=False), encoding='utf-8')

(root / 'inputs' / 'seed.txt').write_text('TOKENGUARD_MARKER_SEED=314159\n', encoding='utf-8')
