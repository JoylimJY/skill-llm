import json
import os
import re
import sys
from pathlib import Path


def safe_read_text(path: Path):
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)


def normalize(s: str):
    return re.sub(r'[^a-z0-9]+', ' ', (s or '').lower()).strip()


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    report_path = workspace / 'memory_report.json'
    db_path = workspace / 'agent_memory.db'

    # Check 1: report exists and is valid JSON
    try:
        if not report_path.exists():
            checks.append({
                'name': 'memory_report_exists',
                'passed': False,
                'detail': 'memory_report.json is missing'
            })
        else:
            try:
                report = json.loads(report_path.read_text(encoding='utf-8', errors='ignore'))
                checks.append({
                    'name': 'memory_report_exists',
                    'passed': True,
                    'detail': 'memory_report.json exists and parsed as JSON'
                })
            except Exception as e:
                report = None
                checks.append({
                    'name': 'memory_report_exists',
                    'passed': False,
                    'detail': f'memory_report.json is not valid JSON: {e}'
                })
    except Exception as e:
        report = None
        checks.append({'name': 'memory_report_exists', 'passed': False, 'detail': str(e)})

    # Check 2: database exists
    try:
        if db_path.exists() and db_path.is_file():
            checks.append({'name': 'database_exists', 'passed': True, 'detail': 'agent_memory.db exists'})
        else:
            checks.append({'name': 'database_exists', 'passed': False, 'detail': 'agent_memory.db is missing'})
    except Exception as e:
        checks.append({'name': 'database_exists', 'passed': False, 'detail': str(e)})

    # Check 3: report contains required fields and reasonable counts
    try:
        if isinstance(report, dict):
            db_used = str(report.get('database_path', ''))
            facts = report.get('facts_recorded')
            lessons = report.get('lessons_recorded')
            entities = report.get('entities_recorded')
            tags = report.get('tags_used')
            names = report.get('tracked_entities')
            ok = bool(db_used) and isinstance(facts, int) and facts >= 3 and isinstance(lessons, int) and lessons >= 2 and isinstance(entities, int) and entities >= 2 and isinstance(tags, list) and len(tags) >= 2 and isinstance(names, list) and len(names) >= 2
            detail = f"db={db_used}, facts={facts}, lessons={lessons}, entities={entities}, tags={tags}, names={names}"
            checks.append({'name': 'report_fields_and_counts', 'passed': ok, 'detail': detail})
        else:
            checks.append({'name': 'report_fields_and_counts', 'passed': False, 'detail': 'report JSON could not be loaded'})
    except Exception as e:
        checks.append({'name': 'report_fields_and_counts', 'passed': False, 'detail': str(e)})

    # Check 4: workspace marker content influenced the result in some way
    try:
        session = workspace / 'session_notes.txt'
        target = workspace / 'memory_target.txt'
        session_text, session_err = safe_read_text(session)
        target_text, target_err = safe_read_text(target)
        combined = ' '.join([t for t in [session_text if isinstance(session_text, str) else None, target_text if isinstance(target_text, str) else None] if t])
        if session_err or target_err:
            checks.append({'name': 'marker_files_present', 'passed': False, 'detail': f'session_err={session_err}; target_err={target_err}'})
        else:
            has_alpha = 'marker session alpha' in normalize(combined)
            has_beta = 'marker target beta' in normalize(combined)
            ok = has_alpha and has_beta
            checks.append({'name': 'marker_files_present', 'passed': ok, 'detail': f'alpha={has_alpha}, beta={has_beta}'})
    except Exception as e:
        checks.append({'name': 'marker_files_present', 'passed': False, 'detail': str(e)})

    total = len(checks)
    passed = sum(1 for c in checks if c.get('passed'))
    score = passed / total if total else 0.0
    result = {'passed': passed == total, 'score': score, 'checks': checks}
    print(json.dumps(result))


if __name__ == '__main__':
    main()
