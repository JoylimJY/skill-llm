import json
import os
import re
from pathlib import Path

workspace = Path(__import__('sys').argv[1])
checks = []


def add_check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})


def safe_read(path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, f"failed to read {path.name}: {e}"


# Check 1: marker.json contains the deterministic marker
try:
    marker_path = workspace / 'marker.json'
    if marker_path.exists():
        text = marker_path.read_text(encoding='utf-8')
        try:
            data = json.loads(text)
            marker_ok = 'OPENCLAW_MARKER_7f3c2a'.lower() in json.dumps(data).lower()
            add_check('marker_present', marker_ok, 'marker.json contains the deterministic marker' if marker_ok else 'marker.json missing expected marker content')
        except Exception as e:
            add_check('marker_present', False, f'could not parse marker.json: {e}')
    else:
        add_check('marker_present', False, 'marker.json is missing')
except Exception as e:
    add_check('marker_present', False, f'unexpected error: {e}')

# Check 2: mcp_config.json references filesystem server and /tmp
try:
    cfg = workspace / 'mcp_config.json'
    if cfg.exists():
        text = cfg.read_text(encoding='utf-8')
        lower = text.lower()
        ok = ('filesystem' in lower) and ('/tmp' in lower)
        add_check('mcp_config_contains_filesystem', ok, 'mcp_config.json references filesystem server and /tmp' if ok else 'mcp_config.json does not appear to configure the filesystem server')
    else:
        add_check('mcp_config_contains_filesystem', False, 'mcp_config.json is missing')
except Exception as e:
    add_check('mcp_config_contains_filesystem', False, f'unexpected error: {e}')

# Check 3: Summary file exists with server IDs and tool count (flexible filename matching)
try:
    output_dir = workspace / 'output'
    summary_file = None
    
    # Look for any file with "summary" in the name
    if output_dir.exists():
        for f in output_dir.iterdir():
            if f.is_file() and re.search(r'summary', f.name, re.IGNORECASE):
                summary_file = f
                break
    
    if summary_file:
        try:
            content = summary_file.read_text(encoding='utf-8')
            normalized = ' '.join(content.lower().split())
            has_server = 'filesystem' in normalized or 'server' in normalized
            has_count = 'tool' in normalized or 'count' in normalized or 'tool_count' in normalized
            add_check('summary_exists', has_server and has_count, f'{summary_file.name} mentions filesystem/server and tool count' if has_server and has_count else f'{summary_file.name} exists but does not clearly summarize server IDs and tool count')
        except Exception as e:
            add_check('summary_exists', False, f'could not read {summary_file.name}: {e}')
    else:
        add_check('summary_exists', False, 'No summary file found in output/ directory')
except Exception as e:
    add_check('summary_exists', False, f'unexpected error: {e}')

# Check 4: Persistent store with counter and item values (flexible filename matching)
try:
    output_dir = workspace / 'output'
    store_file = None
    
    # Look for any file with "state" or "store" in the name
    if output_dir.exists():
        for f in output_dir.iterdir():
            if f.is_file() and re.search(r'(state|store)', f.name, re.IGNORECASE):
                store_file = f
                break
    
    if store_file:
        try:
            data = json.loads(store_file.read_text(encoding='utf-8'))
            # Check for counter value (flexible key names)
            count_ok = False
            if 'counter' in data:
                count_ok = isinstance(data['counter'], (int, float)) and data['counter'] >= 1
            elif 'count' in data:
                count_ok = str(data.get('count', '')).strip() == '1' or data.get('count') == 1
            
            # Check for items list with at least one item
            items_ok = False
            items = data.get('items', [])
            if isinstance(items, list) and len(items) > 0:
                items_ok = any('item' in str(x).lower() for x in items)
            
            add_check('persistent_store_values', count_ok and items_ok, f'{store_file.name} contains counter and item values' if count_ok and items_ok else f'{store_file.name} missing expected counter/item values')
        except Exception as e:
            add_check('persistent_store_values', False, f'could not parse {store_file.name}: {e}')
    else:
        add_check('persistent_store_values', False, 'No persistent state/store file found in output/ directory')
except Exception as e:
    add_check('persistent_store_values', False, f'unexpected error: {e}')

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
passed = passed_count == len(checks)

print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False))