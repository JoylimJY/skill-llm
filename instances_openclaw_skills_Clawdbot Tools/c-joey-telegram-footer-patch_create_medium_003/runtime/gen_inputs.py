import json
from pathlib import Path

root = Path('.')
(root / 'inputs').mkdir(exist_ok=True)

marker_strings = [
    '🧠 Model',
    '💭 Think',
    '📊 Context',
    '--dry-run',
    '--verify',
    '*.bak.telegram-footer.*',
    'openclaw gateway restart',
]

bundle_targets = [
    'dist/agent-runner.runtime-*.js',
    'dist/reply-*.js',
    'dist/compact-*.js',
    'dist/pi-embedded-*.js',
    'dist/plugin-sdk/thread-bindings-*.js',
    'dist/model-selection-*.js',
    'dist/auth-profiles-*.js',
]

# Deterministic input files with marker content for the assistant to use.
(root / 'inputs' / 'marker_strings.txt').write_text('\n'.join(marker_strings) + '\n', encoding='utf-8')
(root / 'inputs' / 'bundle_targets.txt').write_text('\n'.join(bundle_targets) + '\n', encoding='utf-8')
(root / 'inputs' / 'release_boundary.json').write_text(
    json.dumps({
        'validated_version': 'OpenClaw 2026.3.22',
        'validation_boundary': 'live Telegram private-chat acceptance only',
        'static_checks': ['dry-run', 'auto-discover verify', 'smoke test', 'node --check'],
    }, indent=2, ensure_ascii=False) + '\n',
    encoding='utf-8'
)
