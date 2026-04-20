import json
import sys
from pathlib import Path


def norm(s):
    try:
        return ''.join(ch.lower() for ch in str(s) if ch.isalnum())
    except Exception:
        return ''


def safe_read(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore'), None
    except Exception as e:
        return None, str(e)


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    
    checks = []
    ws = workspace

    input_path = ws / 'memory_input.json'
    marker_path = ws / 'task_marker.txt'
    output_path = ws / 'memory_summary.txt'
    db_default = ws / '.agent-memory' / 'memory.db'

    # 1) output file exists
    try:
        exists = output_path.exists()
        detail = 'memory_summary.txt exists' if exists else 'memory_summary.txt is missing'
        checks.append({'name': 'output_exists', 'passed': exists, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'output_exists', 'passed': False, 'detail': f'error checking output file: {e}'})

    # 2) summary mentions marker content
    try:
        text, error = safe_read(output_path)
        if error:
            text = ''
        required = ['atlas-session-42', 'Mina Park', 'Project Juniper']
        found = [r for r in required if norm(r) in norm(text)]
        passed = len(found) >= 2
        detail = f'found markers: {found}; text length={len(text)}'
        checks.append({'name': 'summary_mentions_markers', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'summary_mentions_markers', 'passed': False, 'detail': f'error reading summary: {e}'})

    # 3) input file exists and contains expected markers
    try:
        if input_path.exists():
            data, error = safe_read(input_path)
            if error:
                passed = False
                detail = f'error reading input file: {error}'
            else:
                data = json.loads(data)
                person_ok = norm(data.get('person', '')) == norm('Mina Park') or norm('Mina Park') in norm(data.get('person', ''))
                project_ok = norm(data.get('project', '')) == norm('Project Juniper') or norm('Project Juniper') in norm(data.get('project', ''))
                passed = person_ok and project_ok
                detail = f"person_ok={person_ok}, project_ok={project_ok}"
        else:
            passed = False
            detail = 'memory_input.json is missing'
        checks.append({'name': 'input_file_valid', 'passed': passed, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'input_file_valid', 'passed': False, 'detail': f'error parsing input file: {e}'})

    # 4) database exists in default location or a custom persistent file is created
    try:
        db_exists = db_default.exists()
        detail = f'default db exists={db_exists} at {db_default}'
        checks.append({'name': 'memory_db_present', 'passed': db_exists, 'detail': detail})
    except Exception as e:
        checks.append({'name': 'memory_db_present', 'passed': False, 'detail': f'error checking db path: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed_count == total,
        'score': (passed_count / total) if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': str(e)}]}, ensure_ascii=False))