from pathlib import Path
import json
import random

random.seed(20250311)

workspace = Path('.')

marker = {
    'skill_name': 'telegram-footer-patch',
    'version': 'OpenClaw 2026.3.22',
    'target_file': '/usr/lib/node_modules/openclaw/dist/agent-runner.runtime-BWpOtdxK.js',
    'dry_run': True,
    'verify': True,
    'live_accepted': False,
    'required_restart': 'openclaw gateway restart',
    'rollback_command': 'python3 scripts/revert_reply_footer.py',
    'footer_tokens': ['🧠', '💭 Think', '📊']
}

Path('input_marker.json').write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding='utf-8')

notes = [
    'Dry-run discovered the runtime bundle.',
    'Verification confirmed the marker was written.',
    'Live Telegram acceptance has not been confirmed yet.',
    'Rollback remains available through the revert script.',
]
random.shuffle(notes)
Path('raw_notes.txt').write_text('\n'.join(notes) + '\n', encoding='utf-8')

Path('reference_phrase.txt').write_text(
    'Supported validation boundary: static checks only; live private-chat reply required for final acceptance.\n',
    encoding='utf-8'
)
