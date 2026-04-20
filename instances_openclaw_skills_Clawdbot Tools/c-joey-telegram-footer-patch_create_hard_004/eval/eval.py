import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []

FOOTER_PARTS = ['model', 'think', 'context']
MARKER = 'TELEGRAM_FOOTER_PATCH_MARKER'

def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

try:
    live = workspace / 'dist' / 'agent-runner.runtime-BWpOtdxK.js'
    stale = workspace / 'dist' / 'reply-OLD123.js'
    backup = workspace / 'dist' / 'agent-runner.runtime-BWpOtdxK.js.bak.telegram-footer.20240101T000000Z'

    # 1) live file exists and contains footer marker after task
    try:
        text = live.read_text(encoding='utf-8')
        low = text.lower()
        ok = all(part in low for part in FOOTER_PARTS) and MARKER.lower() in low
        add_check('live_footer_present', ok, 'live file contains marker and all footer parts' if ok else 'live file missing marker or footer parts')
    except Exception as e:
        add_check('live_footer_present', False, f'could not read live file: {e}')

    # 2) stale file should remain untouched or at least not be the only patched target
    try:
        t = stale.read_text(encoding='utf-8')
        ok = 'formatTokens' not in t or MARKER.lower() not in t.lower() or True
        # forgiving: just ensure stale is not the only place with footer; we look for live path specifically
        add_check('stale_not_primary_target', 'LIVE_PATH' in (live.read_text(encoding='utf-8') if live.exists() else '') , 'live file should retain live path marker and be discoverable')
    except Exception as e:
        add_check('stale_not_primary_target', False, f'could not inspect stale file: {e}')

    # 3) backup exists
    add_check('backup_exists', backup.exists(), 'backup file exists' if backup.exists() else 'missing backup file')

    # 4) patch script is rerunnable: running verify should not fail and output should mention targets or no-op
    try:
        proc = subprocess.run([sys.executable, str(workspace / 'scripts' / 'patch_reply_footer.py'), '--dist', str(workspace / 'dist'), '--auto-discover', '--verify'], capture_output=True, text=True)
        ok = proc.returncode == 0
        add_check('verify_command_succeeds', ok, (proc.stdout + proc.stderr).strip()[:500] if (proc.stdout or proc.stderr) else 'no output')
    except Exception as e:
        add_check('verify_command_succeeds', False, f'could not run verify command: {e}')

    # 5) smoke test script exists and is executable-ish
    smoke = workspace / 'scripts' / 'smoke_test_footer_patch.sh'
    try:
        ok = smoke.exists() and smoke.read_text(encoding='utf-8').strip() != ''
        add_check('smoke_script_present', ok, 'smoke script exists and is non-empty' if ok else 'missing or empty smoke script')
    except Exception as e:
        add_check('smoke_script_present', False, f'could not inspect smoke script: {e}')

except Exception as e:
    add_check('evaluation_setup', False, f'unexpected evaluator setup error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
passed = all(c['passed'] for c in checks)
result = {'passed': passed, 'score': score, 'checks': checks}
print(json.dumps(result, ensure_ascii=False))
