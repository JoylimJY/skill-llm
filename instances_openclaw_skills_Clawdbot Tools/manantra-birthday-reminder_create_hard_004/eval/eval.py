import json
import re
from pathlib import Path


def load_text(path):
    try:
        return Path(path).read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(s):
    try:
        return re.sub(r'[^a-z0-9]+', '', s.lower())
    except Exception:
        return ''


def check_person_in_json(data, name, expected_day, expected_month):
    """Check if a person exists in JSON data with matching day/month"""
    if isinstance(data, dict):
        birthdays = data.get('birthdays', [])
        if not birthdays and 'reminders' in data:
            birthdays = data.get('reminders', [])
    elif isinstance(data, list):
        birthdays = data
    else:
        return False
    
    for entry in birthdays:
        if isinstance(entry, dict):
            entry_name = entry.get('name', '')
            if name.lower() in entry_name.lower():
                entry_day = entry.get('day') or entry.get('birthday', '')
                entry_month = entry.get('month') or entry.get('birthday', '')
                
                # Check if day and month match (handle various formats)
                day_match = False
                month_match = False
                
                if isinstance(entry_day, int):
                    day_match = entry_day == expected_day
                elif isinstance(entry_day, str):
                    day_match = str(expected_day).zfill(2) in entry_day or str(expected_day) in entry_day
                
                if isinstance(entry_month, int):
                    month_match = entry_month == expected_month
                elif isinstance(entry_month, str):
                    month_match = str(expected_month).zfill(2) in entry_month or str(expected_month) in entry_month
                
                if day_match and month_match:
                    return True
    
    return False


def main(workspace):
    checks = []
    ws = Path(workspace)
    
    # Look for output files in workspace/data directory
    data_dir = ws / 'data'
    target_files = []
    
    if data_dir.exists():
        for f in data_dir.iterdir():
            if f.is_file() and f.suffix in ['.json', '.md', '.txt']:
                target_files.append(f)
    
    # Check 1: output file exists (JSON or Markdown)
    output_found = False
    output_content = ''
    output_path = None
    output_data = None
    
    for f in target_files:
        if 'birthday' in f.name.lower():
            try:
                content = f.read_text(encoding='utf-8')
                if content and len(content) > 50:  # Non-empty file
                    output_found = True
                    output_content = content
                    output_path = f
                    # Try to parse as JSON
                    try:
                        output_data = json.loads(content)
                    except json.JSONDecodeError:
                        output_data = None
                    break
            except Exception:
                continue
    
    checks.append({
        'name': 'output_file_exists',
        'passed': output_found,
        'detail': f'{output_path} exists' if output_found else 'birthday output file is missing in /workspace/data/'
    })

    # Check 2-5: each person present with normalized date marker
    expected = [
        ('Valentina', 14, 2),   # 14.02
        ('Max', 15, 3),         # 15.03
        ('Lina', 29, 2),        # 29.02
        ('Tom', 1, 12)          # 01.12
    ]

    for name, exp_day, exp_month in expected:
        passed = False
        detail = f'{name} missing or date token not found'
        
        try:
            # First try JSON structured check
            if output_data:
                if check_person_in_json(output_data, name, exp_day, exp_month):
                    passed = True
                    detail = f'{name} present with date token'
            
            # Fallback to text-based fuzzy matching
            if not passed:
                ncontent = normalize(output_content)
                nperson = normalize(name)
                person_ok = nperson in ncontent
                
                # More flexible token matching for day/month
                day_tokens = [str(exp_day).zfill(2), str(exp_day)]
                month_tokens = [str(exp_month).zfill(2), str(exp_month)]
                
                # Check for combined formats like "14.02" or "1402"
                combined_tokens = [f'{exp_day:02d}.{exp_month:02d}', f'{exp_day:02d}{exp_month:02d}']
                
                token_ok = any(normalize(tok) in ncontent for tok in day_tokens + month_tokens + combined_tokens)
                
                passed = bool(person_ok and token_ok)
                detail = f'{name} present with date token' if passed else f'{name} missing or date token not found'
            
            checks.append({'name': f'contains_{name.lower()}', 'passed': passed, 'detail': detail})
        except Exception as e:
            checks.append({'name': f'contains_{name.lower()}', 'passed': False, 'detail': f'error: {e}'})

    # Check 6: marker content from input should not be lost in workspace inputs
    try:
        note_path = ws / 'notes' / 'birthday_notes.txt'
        note_text = note_path.read_text(encoding='utf-8') if note_path.exists() else ''
        passed = 'BDAY-INTAKE-7F3A' in note_text and 'MARKER-AGE-CHECK' in note_text
        checks.append({'name': 'input_marker_present', 'passed': passed, 'detail': 'required markers found in source notes' if passed else 'required markers missing in source notes'})
    except Exception as e:
        checks.append({'name': 'input_marker_present', 'passed': False, 'detail': f'error: {e}'})

    # Check 7: file should have at least 4 entries (flexible for JSON or Markdown)
    try:
        if output_content:
            # Try JSON format
            try:
                data = json.loads(output_content)
                if 'birthdays' in data:
                    entries = len(data['birthdays'])
                elif 'reminders' in data:
                    entries = len(data['reminders'])
                elif isinstance(data, list):
                    entries = len(data)
                else:
                    entries = len(re.findall(r'"name"', output_content))
            except json.JSONDecodeError:
                # Try Markdown format
                entries = len(re.findall(r'^\s*[-*]\s*\*\*.*?\*\*', output_content, flags=re.M))
                if entries == 0:
                    entries = len(re.findall(r'^\s*[-*]\s+\w+', output_content, flags=re.M))
            
            passed = entries >= 4
            checks.append({'name': 'minimum_entries', 'passed': passed, 'detail': f'found {entries} entries' if output_content else 'output file empty or unreadable'})
        else:
            checks.append({'name': 'minimum_entries', 'passed': False, 'detail': 'output file empty or unreadable'})
    except Exception as e:
        checks.append({'name': 'minimum_entries', 'passed': False, 'detail': f'error: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed_count == total,
        'score': (passed_count / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else '.')