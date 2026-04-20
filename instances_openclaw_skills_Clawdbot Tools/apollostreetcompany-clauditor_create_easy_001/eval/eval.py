import json
import os
import re
from pathlib import Path

checks = []
workspace = Path(__import__('sys').argv[1]) if len(__import__('sys').argv) > 1 else Path('.')


def add_check(name, passed, detail):
    checks.append({'name': name, 'passed': bool(passed), 'detail': str(detail)})

try:
    # Look for output files more flexibly - check for JSON files in workspace
    output_file = None
    output_dir = workspace / 'workspace'
    
    if output_dir.exists():
        for f in output_dir.iterdir():
            if f.is_file() and f.suffix == '.json':
                output_file = f
                break
    
    # Also check root workspace for output.txt or similar
    if not output_file:
        for f in workspace.iterdir():
            if f.is_file() and (f.name == 'output.txt' or f.suffix == '.json'):
                output_file = f
                break
    
    if not output_file:
        add_check('output_exists', False, 'no output file found (expected .json or output.txt)')
    else:
        add_check('output_exists', True, f'found output file: {output_file.name}')
        try:
            text = output_file.read_text(encoding='utf-8', errors='replace')
            lowered = ' '.join(text.lower().split())
            
            # Check for audit-related content
            has_audit = ('clauditor' in lowered) or ('audit' in lowered) or ('event' in lowered)
            add_check('output_mentions_audit', has_audit, 'found audit-related wording' if has_audit else 'expected audit-related wording')
            
            # Check for integrity/hash information
            has_hash = ('sha256' in lowered) or ('hash' in lowered) or ('integrity' in lowered)
            add_check('output_has_integrity', has_hash, 'found integrity/hash info' if has_hash else 'expected integrity/hash info')
            
            # Try to parse as JSON and check structure
            try:
                data = json.loads(text)
                if isinstance(data, dict):
                    # Flexible check for event-related keys (case-insensitive)
                    has_events = False
                    for key in data.keys():
                        if re.search(r'event', key, re.IGNORECASE):
                            has_events = True
                            break
                    # Also check if any value is a list that looks like event data
                    if not has_events:
                        for value in data.values():
                            if isinstance(value, list) and len(value) > 0:
                                if isinstance(value[0], dict):
                                    # Check if list items have event-like fields
                                    item_keys = value[0].keys()
                                    if any(re.search(r'event|ts|path|marker', k, re.IGNORECASE) for k in item_keys):
                                        has_events = True
                                        break
                    add_check('output_has_events', has_events, 'found event data' if has_events else 'expected event data')
                else:
                    add_check('output_is_json', False, 'output is not valid JSON object')
            except json.JSONDecodeError:
                add_check('output_is_json', False, 'output is not valid JSON')
                
        except Exception as e:
            add_check('output_readable', False, f'could not read output file: {e}')

    try:
        marker = (workspace / 'input' / 'expected_marker.txt').read_text(encoding='utf-8', errors='replace').strip()
        events = (workspace / 'input' / 'events.log').read_text(encoding='utf-8', errors='replace')
        ok = marker.lower() in events.lower()
        add_check('input_marker_present', ok, 'marker found in events.log' if ok else 'marker missing from events.log')
    except Exception as e:
        add_check('input_marker_present', False, f'failed to inspect inputs: {e}')

    try:
        tmpl = json.loads((workspace / 'input' / 'summary_template.json').read_text(encoding='utf-8', errors='replace'))
        ok = isinstance(tmpl, dict) and 'marker' in tmpl and 'title' in tmpl
        add_check('template_structure', ok, 'template has required keys' if ok else 'template missing required keys')
    except Exception as e:
        add_check('template_structure', False, f'could not parse summary_template.json: {e}')
except Exception as e:
    add_check('eval_internal_error', False, f'unexpected error: {e}')

passed_count = sum(1 for c in checks if c['passed'])
score = passed_count / len(checks) if checks else 0.0
result = {'passed': passed_count == len(checks) and len(checks) > 0, 'score': score, 'checks': checks}
print(json.dumps(result))