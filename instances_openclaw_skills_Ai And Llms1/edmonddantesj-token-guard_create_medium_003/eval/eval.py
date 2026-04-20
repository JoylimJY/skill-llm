import json
import os
import re
from pathlib import Path
import sys


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8'), None
    except Exception as e:
        return None, str(e)


def find_file_in_workspace(ws, possible_names):
    """Search for a file with any of the possible names in common locations."""
    for name in possible_names:
        search_paths = [
            ws / 'workspace' / name,
            ws / name,
            ws / 'workspace' / f'.{name}',
            ws / f'.{name}',
        ]
        for path in search_paths:
            if path.exists():
                return path
    return None


def check_file_exists(path, name):
    try:
        exists = Path(path).exists()
        return {'name': name, 'passed': bool(exists), 'detail': 'exists' if exists else f'missing: {path}'}
    except Exception as e:
        return {'name': name, 'passed': False, 'detail': f'error checking existence: {e}'}


def normalize(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    except Exception:
        return ''


def main():
    checks = []
    try:
        ws = Path(sys.argv[1])
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'workspace-arg', 'passed': False, 'detail': f'missing or invalid workspace argument: {e}'}]}))
        return

    # Find status/report file
    status_path = find_file_in_workspace(ws, ['report.json', 'status.json', 'tokenguard_report.json'])
    # Find cache file
    cache_path = find_file_in_workspace(ws, ['cache.json', '.tokenguard_cache.json', 'tokenguard_cache.json'])

    if status_path:
        checks.append(check_file_exists(status_path, 'status-file-exists'))
    else:
        checks.append({'name': 'status-file-exists', 'passed': False, 'detail': 'missing: could not find report.json or status.json'})

    if cache_path:
        checks.append(check_file_exists(cache_path, 'cache-file-exists'))
    else:
        checks.append({'name': 'cache-file-exists', 'passed': False, 'detail': 'missing: could not find cache.json or .tokenguard_cache.json'})

    # Check status file content
    if status_path:
        status_text, err = safe_read(status_path)
        if status_text is None:
            checks.append({'name': 'status-json-parse', 'passed': False, 'detail': f'cannot read status file: {err}'})
        else:
            try:
                data = json.loads(status_text)
                ok = isinstance(data, dict) and 'models' in data and 'stats' in data
                checks.append({'name': 'status-json-structure', 'passed': ok, 'detail': 'contains models and stats' if ok else 'missing required keys'})
                
                # Check for model quota info (flexible key names)
                try:
                    models = data.get('models', {})
                    has_quota_info = False
                    for model_name, model_data in models.items():
                        if isinstance(model_data, dict):
                            if any(k in model_data for k in ['tpm_limit', 'tokens_used', 'utilization_pct', 'usage_pct', 'requests_count', 'current_usage', 'used_percent']):
                                has_quota_info = True
                                break
                    checks.append({'name': 'status-model-quota-info', 'passed': has_quota_info, 'detail': 'models have quota info' if has_quota_info else 'missing quota info in models'})
                except Exception as e:
                    checks.append({'name': 'status-model-quota-info', 'passed': False, 'detail': f'error reading model info: {e}'})
                
                # Check stats (flexible key names)
                try:
                    stats = data.get('stats', {})
                    blocks = stats.get('blocks', stats.get('total_blocks', -1))
                    fallbacks = stats.get('fallbacks', stats.get('total_fallbacks', -1))
                    ok3 = int(blocks) >= 0 and int(fallbacks) >= 0
                    checks.append({'name': 'status-stats', 'passed': ok3, 'detail': f"blocks={blocks} fallbacks={fallbacks}"})
                except Exception as e:
                    checks.append({'name': 'status-stats', 'passed': False, 'detail': f'error reading stats: {e}'})
            except Exception as e:
                checks.append({'name': 'status-json-parse', 'passed': False, 'detail': f'invalid json: {e}'})
    else:
        checks.append({'name': 'status-json-parse', 'passed': False, 'detail': 'status file not found'})

    # Check cache file content
    if cache_path:
        cache_text, err = safe_read(cache_path)
        if cache_text is None:
            checks.append({'name': 'cache-json-parse', 'passed': False, 'detail': f'cannot read cache file: {err}'})
        else:
            try:
                cache = json.loads(cache_text)
                ok = isinstance(cache, dict) and any(normalize(k) for k in cache.keys())
                checks.append({'name': 'cache-json-structure', 'passed': ok, 'detail': 'cache has keys' if ok else 'cache empty or malformed'})
                
                # Check that cache contains expected structure for duplicate detection
                # Cache should have request hashes or similar tracking data
                try:
                    cache_str = json.dumps(cache, ensure_ascii=False)
                    has_hash_or_tracking = ('hash' in cache_str.lower() or 
                                           'requests' in cache_str.lower() or 
                                           'usage' in cache_str.lower() or
                                           len(cache_str) > 50)  # Non-trivial content
                    checks.append({'name': 'cache-tracking-data', 'passed': has_hash_or_tracking, 'detail': 'cache contains tracking data' if has_hash_or_tracking else 'cache appears empty or malformed'})
                except Exception as e:
                    checks.append({'name': 'cache-tracking-data', 'passed': False, 'detail': f'error scanning cache: {e}'})
            except Exception as e:
                checks.append({'name': 'cache-json-parse', 'passed': False, 'detail': f'invalid json: {e}'})
    else:
        checks.append({'name': 'cache-json-parse', 'passed': False, 'detail': 'cache file not found'})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    score = (passed / total) if total else 0.0
    result = {'passed': passed == total and total > 0, 'score': score, 'checks': checks}
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()