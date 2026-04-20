import json
import os
from pathlib import Path

checks = []
workspace = Path('.')

try:
    peers_path = workspace / 'memory' / 'clawdbot-sync' / 'peers.json'
    passed = peers_path.exists()
    detail = 'peers.json exists' if passed else 'peers.json is missing'
    checks.append({'name': 'peers_file_exists', 'passed': passed, 'detail': detail})
except Exception as e:
    checks.append({'name': 'peers_file_exists', 'passed': False, 'detail': f'error checking peers file: {e}'})

try:
    marker_file = workspace / 'input_marker.txt'
    text = marker_file.read_text(encoding='utf-8', errors='ignore') if marker_file.exists() else ''
    passed = 'sync_marker_input' in text.lower()
    detail = 'marker found in input_marker.txt' if passed else 'marker missing from input_marker.txt'
    checks.append({'name': 'input_marker_present', 'passed': passed, 'detail': detail})
except Exception as e:
    checks.append({'name': 'input_marker_present', 'passed': False, 'detail': f'error reading marker file: {e}'})

try:
    peers = {}
    if peers_path.exists():
        try:
            peers = json.loads(peers_path.read_text(encoding='utf-8', errors='ignore'))
        except Exception as e:
            checks.append({'name': 'peers_json_parse', 'passed': False, 'detail': f'could not parse peers.json: {e}'})
            peers = {}
    peers_text = json.dumps(peers).lower()
    wanted = ['laptop', '100.64.12.34', 'alice', '/workspace/clawd']
    passed = all(str(x).lower() in peers_text for x in wanted)
    detail = 'peer entry contains expected fields' if passed else 'peer entry missing one or more expected fields'
    checks.append({'name': 'peer_entry_content', 'passed': passed, 'detail': detail})
except Exception as e:
    checks.append({'name': 'peer_entry_content', 'passed': False, 'detail': f'error inspecting peers.json: {e}'})

try:
    history_path = workspace / 'memory' / 'clawdbot-sync' / 'history.json'
    text = history_path.read_text(encoding='utf-8', errors='ignore') if history_path.exists() else ''
    passed = 'sync_marker_history_001' in text.lower()
    detail = 'history marker found' if passed else 'history marker missing'
    checks.append({'name': 'history_marker_present', 'passed': passed, 'detail': detail})
except Exception as e:
    checks.append({'name': 'history_marker_present', 'passed': False, 'detail': f'error checking history file: {e}'})

passed_count = sum(1 for c in checks if c.get('passed'))
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks), 'score': score, 'checks': checks}
print(json.dumps(result))