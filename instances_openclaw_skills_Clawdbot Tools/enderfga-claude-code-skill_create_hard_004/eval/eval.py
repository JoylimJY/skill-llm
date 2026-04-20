import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def norm(s):
    return re.sub(r'[^a-z0-9]+', '', s.lower()) if isinstance(s, str) else ''


def main():
    checks = []
    workspace = Path(sys.argv[1])

    # 1) Config file exists and includes both servers
    try:
        p = workspace / 'mcp_config.json'
        if not p.exists():
            checks.append({'name': 'config_exists', 'passed': False, 'detail': 'mcp_config.json is missing'})
        else:
            data = json.loads(p.read_text(encoding='utf-8'))
            servers = data.get('mcpServers', {}) if isinstance(data, dict) else {}
            found_fs = 'filesystem' in servers
            found_gh = 'github' in servers
            checks.append({'name': 'config_servers', 'passed': found_fs and found_gh, 'detail': f'filesystem={found_fs}, github={found_gh}'})
    except Exception as e:
        checks.append({'name': 'config_servers', 'passed': False, 'detail': f'Error reading config: {e}'})

    # 2) Local sessions marker content
    try:
        p = workspace / 'local_sessions.json'
        if not p.exists():
            checks.append({'name': 'local_sessions_exists', 'passed': False, 'detail': 'local_sessions.json is missing'})
        else:
            txt = p.read_text(encoding='utf-8')
            ok = ('local marker alpha' in txt.lower()) and ('local marker beta' in txt.lower())
            checks.append({'name': 'local_sessions_markers', 'passed': ok, 'detail': 'found required local markers' if ok else 'missing one or more local markers'})
    except Exception as e:
        checks.append({'name': 'local_sessions_markers', 'passed': False, 'detail': f'Error reading local sessions: {e}'})

    # 3) Remote sessions marker content
    try:
        p = workspace / 'remote_sessions.json'
        if not p.exists():
            checks.append({'name': 'remote_sessions_exists', 'passed': False, 'detail': 'remote_sessions.json is missing'})
        else:
            txt = p.read_text(encoding='utf-8')
            ok = ('remote marker gamma' in txt.lower()) and ('remote override delta' in txt.lower())
            checks.append({'name': 'remote_sessions_markers', 'passed': ok, 'detail': 'found required remote markers' if ok else 'missing one or more remote markers'})
    except Exception as e:
        checks.append({'name': 'remote_sessions_markers', 'passed': False, 'detail': f'Error reading remote sessions: {e}'})

    # 4) State seed markers
    try:
        p = workspace / 'state_seed.txt'
        if not p.exists():
            checks.append({'name': 'state_seed_exists', 'passed': False, 'detail': 'state_seed.txt is missing'})
        else:
            txt = p.read_text(encoding='utf-8')
            ok = all(m in txt for m in ['OPENCLAW-CLAUDE-CODE-SKILL', 'MERGE_TEST_42', '1337'])
            checks.append({'name': 'state_seed_markers', 'passed': ok, 'detail': 'seed markers verified' if ok else 'one or more seed markers missing'})
    except Exception as e:
        checks.append({'name': 'state_seed_markers', 'passed': False, 'detail': f'Error reading seed file: {e}'})

    # 5) Expected tools metadata
    try:
        p = workspace / 'expected_tools.json'
        if not p.exists():
            checks.append({'name': 'expected_tools_exists', 'passed': False, 'detail': 'expected_tools.json is missing'})
        else:
            data = json.loads(p.read_text(encoding='utf-8'))
            exp = data.get('expected_servers', []) if isinstance(data, dict) else []
            ok = any(norm(x) == 'filesystem' for x in exp) and any(norm(x) == 'github' for x in exp)
            checks.append({'name': 'expected_tools_metadata', 'passed': ok, 'detail': f'expected_servers={exp}'})
    except Exception as e:
        checks.append({'name': 'expected_tools_metadata', 'passed': False, 'detail': f'Error reading metadata: {e}'})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    score = passed / total if total else 0.0
    result = {'passed': passed == total, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
