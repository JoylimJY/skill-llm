import json
import os
import re
import sys
from pathlib import Path

checks = []
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read_text(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f"Could not read {path.name}: {e}"

# Check 1: file exists
try:
    target = workspace / 'mcp_config.json'
    if not target.exists():
        add_check('mcp_config_exists', False, 'mcp_config.json is missing')
    else:
        add_check('mcp_config_exists', True, 'mcp_config.json exists')
except Exception as e:
    add_check('mcp_config_exists', False, f'Exception during existence check: {e}')

# Check 2: parse JSON and validate structure
config = None
try:
    if (workspace / 'mcp_config.json').exists():
        try:
            config = json.loads((workspace / 'mcp_config.json').read_text(encoding='utf-8'))
            add_check('mcp_config_valid_json', True, 'Valid JSON')
        except Exception as e:
            add_check('mcp_config_valid_json', False, f'Invalid JSON: {e}')
    else:
        add_check('mcp_config_valid_json', False, 'Skipped because file is missing')
except Exception as e:
    add_check('mcp_config_valid_json', False, f'Exception during JSON parse: {e}')

# Check 3: expected server names and properties
try:
    if isinstance(config, dict) and isinstance(config.get('mcpServers'), dict):
        servers = config['mcpServers']
        fs = servers.get('filesystem')
        gh = servers.get('github')

        fs_ok = isinstance(fs, dict) and str(fs.get('command', '')).lower().strip() == 'npx' and any('/tmp' in str(x) for x in fs.get('args', []))
        gh_ok = isinstance(gh, dict) and str(gh.get('command', '')).lower().strip() == 'npx' and 'GITHUB_TOKEN' in (gh.get('env') or {})
        
        # Check for 'active' field (boolean true) or 'status' field (string 'active')
        def is_server_active(s):
            if not isinstance(s, dict):
                return False
            # Check 'active' field (boolean)
            if 'active' in s:
                return s['active'] is True
            # Check 'status' field (string)
            if 'status' in s:
                return str(s['status']).lower().strip() == 'active'
            return False
        
        active_ok = is_server_active(fs or {}) and is_server_active(gh or {})

        add_check('filesystem_server_config', fs_ok, f'filesystem config found: {bool(fs)}')
        add_check('github_server_config', gh_ok, f'github config found: {bool(gh)}')
        add_check('servers_marked_active', active_ok, 'Both servers should be active')
    else:
        add_check('server_structure', False, 'mcpServers object missing or malformed')
        add_check('filesystem_server_config', False, 'Cannot validate because structure is malformed')
        add_check('github_server_config', False, 'Cannot validate because structure is malformed')
        add_check('servers_marked_active', False, 'Cannot validate because structure is malformed')
except Exception as e:
    add_check('server_structure', False, f'Exception during server validation: {e}')
    add_check('filesystem_server_config', False, f'Exception during server validation: {e}')
    add_check('github_server_config', False, f'Exception during server validation: {e}')
    add_check('servers_marked_active', False, f'Exception during server validation: {e}')

# Check 4: marker input file exists with expected marker
try:
    marker_path = workspace / 'input_marker.json'
    if not marker_path.exists():
        add_check('input_marker_exists', False, 'input_marker.json is missing')
    else:
        try:
            data = json.loads(marker_path.read_text(encoding='utf-8'))
            marker_ok = 'OPENCLAW_TASK_MARKER_7F3A' in json.dumps(data)
            add_check('input_marker_exists', True, 'input_marker.json exists')
            add_check('input_marker_content', marker_ok, 'Marker content present' if marker_ok else 'Marker content missing')
        except Exception as e:
            add_check('input_marker_exists', True, 'input_marker.json exists')
            add_check('input_marker_content', False, f'Could not parse marker file: {e}')
except Exception as e:
    add_check('input_marker_exists', False, f'Exception during marker validation: {e}')
    add_check('input_marker_content', False, f'Exception during marker validation: {e}')

passed = all(c['passed'] for c in checks)
score = (sum(1 for c in checks if c['passed']) / len(checks)) if checks else 0.0
result = {"passed": passed, "score": score, "checks": checks}
print(json.dumps(result, ensure_ascii=False))