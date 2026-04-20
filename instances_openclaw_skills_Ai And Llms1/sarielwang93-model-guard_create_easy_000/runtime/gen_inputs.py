from pathlib import Path
import json

Path('status.txt').write_text('google-antigravity usage: claude-opus-4-5-thinking 85% left, claude-sonnet-4-5 60% left, gemini-3-flash 100% left\n', encoding='utf-8')
Path('marker.json').write_text(json.dumps({'marker': 'MODEL_GUARD_TEST', 'seed': 42}, indent=2), encoding='utf-8')
