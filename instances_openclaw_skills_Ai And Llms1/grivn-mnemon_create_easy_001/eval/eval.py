import json
import os
import re
import sys
from pathlib import Path


def norm(text):
    try:
        text = text.lower()
        text = re.sub(r'[^a-z0-9]+', ' ', text)
        return ' '.join(text.split())
    except Exception:
        return ''


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    try:
        # Look for any JSON or TXT file that could contain memory output
        candidates = list(workspace.glob('*.json')) + list(workspace.glob('*.txt'))
        found = None
        for p in candidates:
            if p.exists():
                found = p
                break
        
        if found is None:
            checks.append({'name': 'output_file_exists', 'passed': False, 'detail': 'Expected an output file such as output.txt, memory.txt, or a .json file was not found.'})
        else:
            try:
                text = found.read_text(encoding='utf-8', errors='replace')
                
                # Try to parse as JSON if it's a .json file
                if found.suffix == '.json':
                    try:
                        data = json.loads(text)
                        # Check if it has entries structure
                        if isinstance(data, dict) and 'entries' in data:
                            entries = data['entries']
                            if isinstance(entries, list) and len(entries) > 0:
                                entry = entries[0]
                                # Verify required fields exist (accept both 'content' and 'fact' for the memory text)
                                required_fields = ['id', 'category', 'importance', 'entities', 'source']
                                content_fields = ['content', 'fact']  # Accept either field name
                                
                                has_all_fields = all(field in entry for field in required_fields)
                                has_content_field = any(field in entry for field in content_fields)
                                
                                # Get content from either 'content' or 'fact' field
                                content = entry.get('content', entry.get('fact', ''))
                                n = norm(content)
                                wanted = ['project orion', 'release checklist', 'shared docs']
                                has_content = all(term in n for term in wanted)
                                
                                # Check category and importance
                                correct_category = entry.get('category', '').lower() == 'fact'
                                correct_importance = entry.get('importance') == 4
                                
                                ok = has_all_fields and has_content_field and has_content and correct_category and correct_importance
                                detail = 'Found valid memory entry with all required fields.' if ok else f'Output file found at {found.name}, but validation failed.'
                                checks.append({'name': 'output_contains_markers', 'passed': ok, 'detail': detail})
                            else:
                                checks.append({'name': 'output_contains_markers', 'passed': False, 'detail': f'JSON file found but entries list is empty or invalid.'})
                        else:
                            # Fallback to text search for non-standard JSON
                            n = norm(text)
                            wanted = ['project orion', 'release checklist', 'shared docs']
                            ok = all(term in n for term in wanted)
                            detail = 'Found output file and verified key phrases.' if ok else f'Output file found at {found.name}, but required phrases were missing.'
                            checks.append({'name': 'output_contains_markers', 'passed': ok, 'detail': detail})
                    except json.JSONDecodeError:
                        # Not valid JSON, fall back to text search
                        n = norm(text)
                        wanted = ['project orion', 'release checklist', 'shared docs']
                        ok = all(term in n for term in wanted)
                        detail = 'Found output file and verified key phrases.' if ok else f'Output file found at {found.name}, but required phrases were missing.'
                        checks.append({'name': 'output_contains_markers', 'passed': ok, 'detail': detail})
                else:
                    # Text file - use text search
                    n = norm(text)
                    wanted = ['project orion', 'release checklist', 'shared docs']
                    ok = all(term in n for term in wanted)
                    detail = 'Found output file and verified key phrases.' if ok else f'Output file found at {found.name}, but required phrases were missing.'
                    checks.append({'name': 'output_contains_markers', 'passed': ok, 'detail': detail})
            except Exception as e:
                checks.append({'name': 'output_file_exists', 'passed': False, 'detail': f'Error while reading output file: {type(e).__name__}: {e}'})
                checks.append({'name': 'output_contains_markers', 'passed': False, 'detail': 'Skipped due to earlier error.'})
    except Exception as e:
        checks.append({'name': 'output_file_exists', 'passed': False, 'detail': f'Error while checking output file: {type(e).__name__}: {e}'})
        checks.append({'name': 'output_contains_markers', 'passed': False, 'detail': 'Skipped due to earlier error.'})

    try:
        marker_file = workspace / 'task_context.txt'
        if not marker_file.exists():
            checks.append({'name': 'input_marker_present', 'passed': False, 'detail': 'task_context.txt is missing.'})
        else:
            text = marker_file.read_text(encoding='utf-8', errors='replace')
            ok = 'PROJECT_ORION_RELEASE_CHECKLIST' in text
            checks.append({'name': 'input_marker_present', 'passed': ok, 'detail': 'Marker content verified.' if ok else 'Marker content was not found in task_context.txt.'})
    except Exception as e:
        checks.append({'name': 'input_marker_present', 'passed': False, 'detail': f'Error while checking marker file: {type(e).__name__}: {e}'})

    try:
        # Simple output format sanity check if a result file exists.
        result_files = [p for p in workspace.iterdir() if p.is_file() and p.suffix in {'.json', '.txt', '.log'}]
        ok = len(result_files) >= 1
        checks.append({'name': 'workspace_has_files', 'passed': ok, 'detail': f'Workspace contains {len(result_files)} candidate file(s).' if ok else 'No candidate files found in workspace.'})
    except Exception as e:
        checks.append({'name': 'workspace_has_files', 'passed': False, 'detail': f'Error while scanning workspace: {type(e).__name__}: {e}'})

    passed = all(c.get('passed', False) for c in checks) if checks else False
    score = (sum(1 for c in checks if c.get('passed', False)) / len(checks)) if checks else 0.0
    print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))


if __name__ == '__main__':
    main()