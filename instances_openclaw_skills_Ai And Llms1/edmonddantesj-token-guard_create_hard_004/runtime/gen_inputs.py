from pathlib import Path
import json
import random

random.seed(1337)
root = Path('.')
(root / 'input').mkdir(exist_ok=True)

spec = {
    'marker': 'TOKEN_GUARD_READY',
    'models': ['gemini-3-flash', 'claude-sonnet', 'gpt-4o'],
    'request_text': 'Hello world! 这是一个测试。Please estimate tokens and guard quota.',
    'custom_quota': {'model': 'toy-model', 'tpm_limit': 12345}
}

(root / 'input' / 'token_guard_seed.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
(root / 'input' / 'status_marker.txt').write_text('TOKEN_GUARD_READY\n', encoding='utf-8')
(root / 'input' / 'usage_sample.json').write_text(json.dumps({'gemini-3-flash': {'used_this_minute': 750000, 'remaining': 250000}}, indent=2), encoding='utf-8')
