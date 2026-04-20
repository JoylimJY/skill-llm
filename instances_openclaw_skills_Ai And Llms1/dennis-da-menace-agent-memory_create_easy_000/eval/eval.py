import json
import sys
import re
from pathlib import Path


def safe_read(path: Path):
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        return None, str(e)


def normalize(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def main():
    workspace = Path(sys.argv[1])
    checks = []

    # Check 1: output directory exists
    try:
        passed = (workspace / 'output').exists()
        checks.append({
            'name': 'output directory exists',
            'passed': passed,
            'detail': 'output directory found' if passed else 'output directory missing'
        })
    except Exception as e:
        checks.append({'name': 'output directory exists', 'passed': False, 'detail': f'error: {e}'})

    # Check 2: input markers file exists and contains marker content
    try:
        path = workspace / 'input' / 'markers.json'
        if not path.exists():
            checks.append({'name': 'input markers present', 'passed': False, 'detail': 'input/markers.json missing'})
        else:
            try:
                data = json.loads(path.read_text(encoding='utf-8'))
                passed = all(k in data for k in ['session_id', 'person_name', 'project_name'])
                checks.append({
                    'name': 'input markers present',
                    'passed': passed,
                    'detail': 'marker keys present' if passed else 'marker keys missing'
                })
            except Exception as e:
                checks.append({'name': 'input markers present', 'passed': False, 'detail': f'parse error: {e}'})
    except Exception as e:
        checks.append({'name': 'input markers present', 'passed': False, 'detail': f'error: {e}'})

    # Check 3: output files have evidence of remembered fact / lesson / entity
    try:
        output_dir = workspace / 'output'
        if not output_dir.exists():
            checks.append({'name': 'memory output content', 'passed': False, 'detail': 'output directory missing'})
        else:
            # Find all output files (json or txt)
            candidates = list(output_dir.glob('*.json')) + list(output_dir.glob('*.txt'))
            
            if not candidates:
                checks.append({'name': 'memory output content', 'passed': False, 'detail': 'no expected output file found'})
            else:
                # Combine content from ALL output files
                all_content = ''
                for p in candidates:
                    try:
                        content = p.read_text(encoding='utf-8')
                        all_content += content + ' '
                    except Exception as e:
                        pass
                
                if not all_content:
                    checks.append({'name': 'memory output content', 'passed': False, 'detail': 'could not read output files'})
                else:
                    n = normalize(all_content)
                    # Check for required memory sections (flexible matching for underscores/spaces)
                    has_fact = 'remembered fact' in n or 'remembered_facts' in n or 'rememberedfacts' in n
                    has_lesson = 'learned lesson' in n or 'learned_lessons' in n or 'learnedlessons' in n
                    has_entity = 'tracked entity' in n or 'tracked_entities' in n or 'trackedentities' in n
                    
                    passed = has_fact and has_lesson and has_entity
                    checks.append({
                        'name': 'memory output content',
                        'passed': passed,
                        'detail': 'contains required memory sections' if passed else 'missing one or more required memory sections'
                    })
    except Exception as e:
        checks.append({'name': 'memory output content', 'passed': False, 'detail': f'error: {e}'})

    # Check 4: output mentions the marker ORCHID-42 or project/person terms
    try:
        output_dir = workspace / 'output'
        if not output_dir.exists():
            checks.append({'name': 'marker propagated', 'passed': False, 'detail': 'output directory missing'})
        else:
            # Find all output files (json or txt)
            candidates = list(output_dir.glob('*.json')) + list(output_dir.glob('*.txt'))
            
            all_content = ''
            for p in candidates:
                try:
                    content = p.read_text(encoding='utf-8')
                    all_content += content + ' '
                except Exception as e:
                    pass
            
            if not all_content:
                checks.append({'name': 'marker propagated', 'passed': False, 'detail': 'no output file found to check'})
            else:
                n = normalize(all_content)
                passed = ('orchid 42' in n) or ('ava chen' in n) or ('orchid' in n)
                checks.append({
                    'name': 'marker propagated',
                    'passed': passed,
                    'detail': 'marker content detected' if passed else 'marker content not detected'
                })
    except Exception as e:
        checks.append({'name': 'marker propagated', 'passed': False, 'detail': f'error: {e}'})

    total = len(checks)
    passed_count = sum(1 for c in checks if c.get('passed'))
    result = {
        'passed': passed_count == total,
        'score': passed_count / total if total else 0.0,
        'checks': checks,
    }
    print(json.dumps(result))


if __name__ == '__main__':
    main()