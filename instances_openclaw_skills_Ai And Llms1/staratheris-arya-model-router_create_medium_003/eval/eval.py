import json
import os
import re
import sys
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, f"read failed: {e}"


try:
    readme_path = workspace / 'skills' / 'arya-model-router' / 'README.md'
    router_path = workspace / 'skills' / 'arya-model-router' / 'router.py'
    state_path = workspace / 'skills' / 'arya-model-router' / 'state.json'
    rules_path = workspace / 'skills' / 'arya-model-router' / 'rules.json'

    ok = True
    details = []
    for p in [readme_path, router_path, state_path, rules_path]:
        if not p.exists():
            ok = False
            details.append(f"missing {p.name}")
    add_check('required files exist', ok, '; '.join(details) if details else 'all present')
except Exception as e:
    add_check('required files exist', False, f'exception: {e}')

try:
    text = router_path.read_text(encoding='utf-8') if router_path.exists() else ''
    lowered = re.sub(r'\s+', ' ', text.lower())
    ok = 'router force' in lowered and 'forced_level' in lowered and 'router force off' in lowered
    add_check('router force support implemented', ok, 'found force command and forced_level handling' if ok else 'missing force override behavior')
except Exception as e:
    add_check('router force support implemented', False, f'exception: {e}')

try:
    readme = readme_path.read_text(encoding='utf-8') if readme_path.exists() else ''
    ok = all(k in readme.lower() for k in ['router force cheap', 'router force default', 'router force pro', 'router force ultra', 'router force off'])
    add_check('README documents force commands', ok, 'force commands documented' if ok else 'documentation incomplete')
except Exception as e:
    add_check('README documents force commands', False, f'exception: {e}')

try:
    import subprocess
    env = os.environ.copy()
    router_file = workspace / 'skills' / 'arya-model-router' / 'router.py'
    cmd = ['python3', str(router_file), '--text', 'router force pro', '--context-chars', '99999']
    res = subprocess.run(cmd, cwd=str(workspace), capture_output=True, text=True, timeout=20)
    data = json.loads(res.stdout.strip() or '{}')
    ok = str(data.get('forced_level', data.get('level', ''))).lower() == 'pro' or 'pro' in str(data).lower()
    add_check('force command returns confirmation', ok, f"stdout={res.stdout.strip()[:200]}")
except Exception as e:
    add_check('force command returns confirmation', False, f'exception: {e}')

try:
    import subprocess
    state_file = workspace / 'skills' / 'arya-model-router' / 'state.json'
    before = json.loads(state_file.read_text(encoding='utf-8')) if state_file.exists() else {}
    subprocess.run(['python3', str(workspace / 'skills' / 'arya-model-router' / 'router.py'), '--text', 'router force pro'], cwd=str(workspace), capture_output=True, text=True, timeout=20)
    out = subprocess.run(['python3', str(workspace / 'skills' / 'arya-model-router' / 'router.py'), '--text', 'simple hello', '--context-chars', '10'], cwd=str(workspace), capture_output=True, text=True, timeout=20)
    data = json.loads(out.stdout.strip() or '{}')
    ok = data.get('level') == 'pro'
    add_check('forced level overrides normal routing', ok, f"routed level={data.get('level')} after force")
except Exception as e:
    add_check('forced level overrides normal routing', False, f'exception: {e}')

try:
    import subprocess
    subprocess.run(['python3', str(workspace / 'skills' / 'arya-model-router' / 'router.py'), '--text', 'router force off'], cwd=str(workspace), capture_output=True, text=True, timeout=20)
    out = subprocess.run(['python3', str(workspace / 'skills' / 'arya-model-router' / 'router.py'), '--text', 'simple hello', '--context-chars', '10'], cwd=str(workspace), capture_output=True, text=True, timeout=20)
    data = json.loads(out.stdout.strip() or '{}')
    ok = data.get('level') in {'cheap', 'default'}
    add_check('force off clears persistent override', ok, f"routed level={data.get('level')} after force off")
except Exception as e:
    add_check('force off clears persistent override', False, f'exception: {e}')

try:
    score = sum(1 for c in checks if c['passed']) / max(1, len(checks))
    passed = all(c['passed'] for c in checks)
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))
except Exception:
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}, ensure_ascii=False))
