from pathlib import Path
import json

# Deterministic input generation with fixed content markers
Path('input_context.txt').write_text(
    'OpenClaw Telegram footer patch\n'
    'Marker: Model + Think + Context\n'
    'Validation boundary: live Telegram private-chat reply\n',
    encoding='utf-8'
)

Path('reference_notes.txt').write_text(
    'Required flow: dry-run, backup, rollback, restart guidance\n'
    'Expected tone: clear, professional, concise\n',
    encoding='utf-8'
)

payload = {
    'feature_name': 'telegram-footer-patch',
    'marker_phrase': 'Model + Think + Context',
    'must_mention': ['dry-run', 'backup', 'rollback', 'restart'],
}
Path('reference_data.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
