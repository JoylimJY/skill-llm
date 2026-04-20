import json
import os
import re
import sys
from pathlib import Path


def main():
    checks = []
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    def add(name, passed, detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})

    try:
        # Check for task package JSON output
        pkg_path = workspace / 'task_package.json'
        if not pkg_path.exists():
            add('task_package_exists', False, 'task_package.json is missing')
        else:
            try:
                content = pkg_path.read_text(encoding='utf-8')
                if not content.strip():
                    add('task_package_exists', False, 'task_package.json is empty')
                else:
                    pkg = json.loads(content)
                    add('task_package_exists', True, 'task_package.json exists and is valid JSON')
                    
                    # Check required fields in task package (fuzzy match keys)
                    required_fields = ['category', 'prompt', 'dockerfile', 'gen_inputs_script', 'setup_script', 'eval_script', 'expected']
                    pkg_keys = list(pkg.keys())
                    missing_fields = [f for f in required_fields if not any(f.lower() in k.lower() for k in pkg_keys)]
                    add('task_package_fields', len(missing_fields) == 0, 
                        'All required fields present' if not missing_fields else f'Missing fields: {missing_fields}')
                    
                    # Check that prompt mentions key concepts (case-insensitive fuzzy match)
                    prompt_text = str(pkg.get('prompt', ''))
                    prompt_ok = (re.search(r'prescription|soul|frankenstein', prompt_text, re.IGNORECASE) is not None)
                    add('task_package_prompt', prompt_ok, 'prompt mentions relevant concepts' if prompt_ok else 'prompt lacks required concepts')
                    
                    # Check that gen_inputs_script is non-empty (lenient)
                    gen_script = str(pkg.get('gen_inputs_script', ''))
                    gen_ok = len(gen_script.strip()) > 10
                    add('task_package_gen_script', gen_ok, 'gen_inputs_script is non-empty' if gen_ok else 'gen_inputs_script is empty')
                    
                    # Check that dockerfile is non-empty (lenient)
                    dockerfile = str(pkg.get('dockerfile', ''))
                    docker_ok = len(dockerfile.strip()) > 10
                    add('task_package_dockerfile', docker_ok, 'dockerfile is non-empty' if docker_ok else 'dockerfile is empty')
                    
                    # Check that eval_script is non-empty (lenient)
                    eval_script = str(pkg.get('eval_script', ''))
                    eval_ok = len(eval_script.strip()) > 10
                    add('task_package_eval_script', eval_ok, 'eval_script is non-empty' if eval_ok else 'eval_script is empty')
                    
                    # Check that expected field exists and is non-empty
                    expected = pkg.get('expected', {})
                    expected_ok = isinstance(expected, dict) and len(expected) > 0
                    add('task_package_expected', expected_ok, 'expected field is a non-empty dict' if expected_ok else 'expected field is missing or empty')
                    
                    # Check for marker content in gen_inputs_script (case-insensitive, fuzzy)
                    has_markers = re.search(r'marker|MARKER', gen_script, re.IGNORECASE) is not None
                    add('task_package_markers', has_markers, 'gen_inputs_script includes marker content' if has_markers else 'gen_inputs_script lacks marker content')
                    
            except json.JSONDecodeError as e:
                add('task_package_exists', False, f'task_package.json is malformed JSON: {e}')
            except Exception as e:
                add('task_package_exists', False, f'error reading task_package.json: {e}')

        # Ensure agent did NOT create task completion outputs (wrong behavior)
        wrong_outputs = [
            workspace / 'memory' / 'soul' / 'prescription.json',
            workspace / 'output.txt',
            workspace / 'memory' / 'soul' / 'interview-log.md'
        ]
        wrong_created = any(p.exists() for p in wrong_outputs)
        add('no_wrong_outputs', not wrong_created, 
            'Agent correctly did not create task completion outputs' if not wrong_created else 
            'Agent incorrectly created task completion outputs instead of task package')

        try:
            score = sum(1 for c in checks if c['passed']) / len(checks) if checks else 0.0
            passed = all(c['passed'] for c in checks)
        except Exception:
            score = 0.0
            passed = False
        print(json.dumps({'passed': passed, 'score': score, 'checks': checks}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'passed': False, 'score': 0.0, 'checks': [{'name': 'fatal', 'passed': False, 'detail': str(e)}]}, ensure_ascii=False))


if __name__ == '__main__':
    main()